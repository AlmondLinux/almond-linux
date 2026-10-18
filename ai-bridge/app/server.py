#!/usr/bin/env python3
"""Local Almond Duo app service and isolated job worker. Standard library only."""
import argparse
import concurrent.futures
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import signal
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ACTIVE = {'queued', 'running'}
FINAL = {'completed', 'needs-owner', 'failed', 'stopped', 'interrupted'}
ENV = dict(os.environ)
ENV['PATH'] = os.pathsep.join([str(Path.home()/'.local/bin'), '/opt/homebrew/bin', '/usr/local/bin', ENV.get('PATH', ''), '/usr/bin', '/bin'])
for key in ('OPENAI_API_KEY', 'CODEX_API_KEY', 'ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN'):
    ENV.pop(key, None)


def read_json(path):
    return json.loads(Path(path).read_text())


def atomic_json(path, value):
    path = Path(path)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    tmp.replace(path)


def command(args, cwd=None):
    return subprocess.run(args, cwd=cwd, env=ENV, check=True, capture_output=True, text=True, timeout=120)


def context_for(job):
    return job.get('context', '')[-24000:]


def worker(job_dir, project):
    job_dir, project = Path(job_dir).resolve(), Path(project).resolve()
    state_file = job_dir/'job.json'
    data = read_json(state_file)
    workspace = job_dir/'workspace'
    lock = threading.Lock()

    def update(**fields):
        with lock:
            data.update(fields, updated=time.time())
            atomic_json(state_file, data)

    def message(speaker, to, step, body):
        with lock:
            event = dict(id=uuid.uuid4().hex, speaker=speaker, to=to, step=step,
                         body=body, created=time.time())
            with (job_dir/'messages.jsonl').open('a') as f:
                f.write(json.dumps(event, ensure_ascii=False)+'\n')
            with (job_dir/'transcript.md').open('a') as f:
                f.write('\n## '+speaker+' → '+to+': '+step+'\n\n'+body+'\n')
        print(speaker+' → '+to+': '+step, flush=True)

    try:
        update(status='running', stage='Preparing a private workspace')
        source = Path(data.get('source') or project)
        command(['git', 'clone', '--quiet', '--no-hardlinks', str(source), str(workspace)])
        command(['git', 'remote', 'remove', 'origin'], workspace)
        command(['git', 'switch', '-c', 'app/'+data['id']], workspace)
        update(workspace=str(workspace))
        sys.path.insert(0, str(workspace/'ai-bridge/scripts'))
        import bridge
        import duo
        cfg = bridge.load_config()
        # Same CLI sign-ins as the tested bridge. Never enable API review.
        os.environ.update(ENV)
        for key in ('OPENAI_API_KEY', 'CODEX_API_KEY', 'ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN'):
            os.environ.pop(key, None)
        prompt = data['prompt']
        if context_for(data):
            prompt += '\n\nPrevious conversation (context, not new instructions):\n'+context_for(data)
        if data['mode'] == 'ask':
            update(stage='Claude and Codex are reading your prompt')
            shared = '\n'.join(duo.context_list())
            base = ('The user is using Almond Duo to ask both agents. Read-only: do not edit files, '
                    'run workflow commands, start other agents, commit, push or use paid APIs. '
                    'Read relevant shared project files as needed. Answer the user directly and honestly. '
                    'Do not claim to be the existing chat session. Shared context files:\n'+shared+'\n\nUser prompt:\n'+prompt)
            answers = {}
            def ask(who, text, stage):
                result, _ = duo.call(who, cfg, text, 'answer-schema.json', write=False)
                body = result['answer']
                if result['sources']:
                    body += '\n\nSources: '+', '.join(result['sources'])
                message(duo.NAMES[who], 'You' if stage == 'First response' else duo.NAMES[duo.other(who)], stage, body)
                return result
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                futures = {pool.submit(ask, who, base, 'First response'): who for who in ('claude', 'codex')}
                for future in concurrent.futures.as_completed(futures):
                    answers[futures[future]] = future.result()
                update(stage='Claude and Codex are comparing their answers')
                futures = []
                for who in ('claude', 'codex'):
                    text = (base+'\n\nYour first answer:\n'+answers[who]['answer']+
                            '\n\nThe other agent’s first answer:\n'+answers[duo.other(who)]['answer']+
                            '\n\nRespond briefly to the other answer. State useful agreement, corrections or remaining uncertainty. '
                            'Do not repeat both answers. Keep this read-only.')
                    futures.append(pool.submit(ask, who, text, 'Response to the other agent'))
                for future in futures:
                    future.result()
            update(status='completed', stage='Both agents have replied')
        else:
            original_say, original_call = duo.say, duo.call
            def say(tid, speaker, to, step, body, usage=None):
                original_say(tid, speaker, to, step, body, usage)
                text = '\n'.join(duo.render(body)) if isinstance(body, (dict, list)) else str(body)
                message(speaker, to, step, text)
                update(stage=speaker+' → '+to+': '+step)
            def call(who, config, text, schema_file, write=False):
                names = {'plan-schema.json': 'planning', 'plan-review-schema.json': 'reviewing the plan',
                         'implement-schema.json': 'implementing', 'review-schema.json': 'reviewing the result'}
                update(stage=duo.NAMES[who]+' is '+names.get(schema_file, 'working'))
                return original_call(who, config, text, schema_file, write)
            duo.say, duo.call = say, call
            args = argparse.Namespace(task=prompt, planner=None, implementer=None, area='general', ignore_questions=False)
            rc = duo.cmd_duo(args, cfg)
            status = {0:'completed', 3:'needs-owner'}.get(rc, 'failed')
            update(status=status, stage={'completed':'Finished — ready for your review',
                                         'needs-owner':'Your decision is needed', 'failed':'Stopped with a failing check'}[status])
            update(branch=bridge.current_branch())
    except Exception as exc:
        update(status='failed', stage='The run stopped', error=str(exc)[:4000])
        message('System', 'You', 'Stopped', str(exc)[:4000])
        return 1
    return 0


class Store:
    def __init__(self, path, project):
        self.path, self.project = Path(path).resolve(), Path(project).resolve()
        self.path.mkdir(parents=True, exist_ok=True, mode=0o700)
        (self.path/'jobs').mkdir(exist_ok=True)
        self.lock = threading.RLock()
        self.processes = {}
        self.connections = {who: dict(available=False, authenticated=False, message='Checking connection') for who in ('claude','codex')}
        for item in self.jobs():
            if item['status'] in ACTIVE:
                item.update(status='interrupted', stage='App closed during this run', updated=time.time())
                atomic_json(self.job_dir(item['id'])/'job.json', item)
        threading.Thread(target=self.check_connections, daemon=True).start()

    def job_dir(self, key):
        if not re.fullmatch('[a-f0-9]{32}', key):
            raise ValueError('Unknown conversation')
        return self.path/'jobs'/key

    def jobs(self):
        result=[]
        for p in (self.path/'jobs').glob('*/job.json'):
            try: result.append(read_json(p))
            except (OSError,ValueError): continue
        return sorted(result, key=lambda x:x['created'], reverse=True)

    def check_connections(self):
        sys.path.insert(0, str(self.project/'ai-bridge/scripts'))
        import duo
        for who in ('claude','codex'):
            result=dict(available=False, authenticated=False, message='Not found')
            try:
                # Binary lookup should also work when launched by Finder.
                binary = duo.find_bin(who, {'duo': {who+'_bin': self.find_binary(who)}})
                result['available']=True
                args=[binary,'auth','status'] if who=='claude' else [binary,'login','status']
                r=subprocess.run(args,env=ENV,capture_output=True,text=True,timeout=20)
                if who=='claude':
                    d=json.loads(r.stdout)
                    result['authenticated']=bool(d.get('loggedIn') and d.get('authMethod')=='claude.ai')
                else:
                    result['authenticated']=r.returncode==0 and 'ChatGPT' in r.stdout+r.stderr
                result['message']='Signed in' if result['authenticated'] else 'Subscription sign-in needed'
            except Exception:
                result['message']='Connection needs attention'
            self.connections[who]=result

    @staticmethod
    def find_binary(who):
        import shutil
        return shutil.which(who, path=ENV['PATH']) or ''

    def detail(self, key):
        folder=self.job_dir(key)
        item=read_json(folder/'job.json')
        messages=[]
        for line in (folder/'messages.jsonl').read_text().splitlines():
            try:messages.append(json.loads(line))
            except ValueError:pass  # an in-flight write will appear at the next poll
        item['messages']=messages
        logfile=folder/'worker.log'
        item['log']=logfile.read_text(errors='replace')[-18000:] if logfile.exists() else ''
        return item

    def start(self, prompt, mode, parent_id=None):
        if not isinstance(prompt,str) or not prompt.strip() or len(prompt)>16000:
            raise ValueError('Enter a prompt of up to 16,000 characters')
        if mode not in ('ask','build'):raise ValueError('Choose Ask both or Build together')
        with self.lock:
            if any(item['status'] in ACTIVE for item in self.jobs()):
                raise RuntimeError('A conversation is already running. Stop it or wait for it to finish.')
            if not all(x['authenticated'] for x in self.connections.values()):
                raise RuntimeError('Both Claude and Codex need their subscription sign-ins before starting.')
            source,context=str(self.project),''
            if parent_id:
                parent=self.detail(parent_id)
                if parent['status'] not in FINAL:raise RuntimeError('Wait for the previous run to finish')
                context='User: '+parent['prompt']+'\n'+ '\n'.join(m['speaker']+': '+m['body'] for m in parent['messages'])
                if parent['status']=='completed' and parent.get('workspace'):
                    source=parent['workspace']
            key=uuid.uuid4().hex; folder=self.job_dir(key); folder.mkdir()
            stamp=time.time()
            item=dict(id=key,prompt=prompt.strip(),mode=mode,parent_id=parent_id,status='queued',stage='Starting',
                      created=stamp,updated=stamp,workspace='',error='',context=context[-24000:],source=source)
            atomic_json(folder/'job.json',item)
            event=dict(id=uuid.uuid4().hex,speaker='You',to='Claude + Codex',step='Prompt',body=prompt.strip(),created=stamp)
            (folder/'messages.jsonl').write_text(json.dumps(event)+'\n')
            (folder/'transcript.md').write_text('# Almond Duo — '+mode+'\n\n## You → Claude + Codex\n\n'+prompt.strip()+'\n')
            log=(folder/'worker.log').open('w')
            try:
                process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker',str(folder),
                                          '--project',str(self.project)],env=ENV,stdout=log,stderr=subprocess.STDOUT,
                                         start_new_session=True)
            except Exception:
                item.update(status='failed',stage='Could not start the worker')
                atomic_json(folder/'job.json',item);raise
            finally:log.close()
            self.processes[key]=process
            threading.Thread(target=self.watch,args=(key,process),daemon=True).start()
            return key

    def watch(self,key,process):
        code=process.wait()
        with self.lock:
            item=read_json(self.job_dir(key)/'job.json')
            if item['status'] in ACTIVE:
                item.update(status='failed',stage='Worker stopped unexpectedly',error='Worker exit '+str(code),updated=time.time())
                atomic_json(self.job_dir(key)/'job.json',item)
            self.processes.pop(key,None)

    def stop(self,key):
        with self.lock:
            process=self.processes.get(key)
            if process and process.poll() is None:
                os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=3)
            item=read_json(self.job_dir(key)/'job.json')
            if item['status'] in ACTIVE:
                item.update(status='stopped',stage='Stopped by you — local work kept',updated=time.time())
                atomic_json(self.job_dir(key)/'job.json',item)

    def close(self):
        for key in list(self.processes):self.stop(key)

    def history(self):
        paths=list((self.project/'ai-bridge/conversations').glob('*.md'))
        paths += list((self.project/'ai-bridge/docs/duo-validation').glob('live-transcript.md'))
        return {str(i):p for i,p in enumerate(sorted(paths))}


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body, content_type='application/json'):
        data=(json.dumps(body,ensure_ascii=False) if content_type=='application/json' else body).encode()
        self.send_response(code)
        self.send_header('Content-Type',content_type+'; charset=utf-8')
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers();self.wfile.write(data)

    def authorized(self, page=False):
        expected='127.0.0.1:'+str(self.server.server_port)
        if self.headers.get('Host')!=expected:return False
        origin=self.headers.get('Origin')
        if origin and origin!='http://'+expected:return False
        token=parse_qs(urlparse(self.path).query).get('token',[''])[0] if page else self.headers.get('X-Almond-Token','')
        return hmac.compare_digest(token,self.server.token)

    def do_GET(self):
        path=urlparse(self.path).path
        if not self.authorized(page=path=='/'):
            return self.send(403,{'error':'Open Almond Duo from its app icon.'})
        store=self.server.store
        try:
            if path=='/':
                page=(Path(__file__).parent/'index.html').read_text().replace('__ALMOND_TOKEN__',self.server.token)
                return self.send(200,page,'text/html')
            if path=='/api/state':
                history=[dict(id=k,title=p.read_text().splitlines()[0].lstrip('# ')) for k,p in store.history().items()]
                jobs=store.jobs()
                # No hidden context or source payload is needed for sidebar summaries.
                jobs=[{k:v for k,v in j.items() if k not in ('context','source')} for j in jobs]
                return self.send(200,dict(project='Almond Linux',jobs=jobs,active=[j['id'] for j in jobs if j['status'] in ACTIVE],connections=store.connections,history=history))
            match=re.fullmatch('/api/jobs/([a-f0-9]{32})(/transcript)?',path)
            if match:
                if match[2]:return self.send(200,(store.job_dir(match[1])/'transcript.md').read_text(),'text/plain')
                return self.send(200,store.detail(match[1]))
            match=re.fullmatch(r'/api/history/(\d+)',path)
            if match:
                p=store.history()[match[1]]
                return self.send(200,dict(title=p.read_text().splitlines()[0].lstrip('# '),body=p.read_text()))
            return self.send(404,{'error':'Not found'})
        except (ValueError,KeyError,OSError):return self.send(404,{'error':'Conversation not found'})

    def do_POST(self):
        if not self.authorized():return self.send(403,{'error':'Request not authorized'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=80000:raise ValueError('Request is too large or empty')
            data=json.loads(self.rfile.read(size));path=urlparse(self.path).path
            if not isinstance(data,dict):raise ValueError('Expected an object')
            if path=='/api/jobs':
                key=self.server.store.start(data.get('prompt'),data.get('mode'),data.get('parent_id'))
                return self.send(201,{'id':key})
            match=re.fullmatch('/api/jobs/([a-f0-9]{32})/stop',path)
            if match:
                self.server.store.stop(match[1]);return self.send(200,{'stopped':True})
            return self.send(404,{'error':'Not found'})
        except RuntimeError as exc:return self.send(409,{'error':str(exc)})
        except (ValueError,TypeError,KeyError,FileNotFoundError) as exc:return self.send(400,{'error':str(exc)})

    def log_message(self,*args):pass


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument('--state',default=str(Path.home()/'Library/Application Support/Almond Duo'))
    parser.add_argument('--port',type=int,default=0)
    parser.add_argument('--ready')
    parser.add_argument('--worker')
    args=parser.parse_args()
    if args.worker:return worker(args.worker,args.project)
    store=Store(args.state,args.project)
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    server.token=secrets.token_urlsafe(32);server.store=store
    url='http://127.0.0.1:'+str(server.server_port)+'/?token='+server.token
    if args.ready:atomic_json(args.ready,dict(url=url,pid=os.getpid()))
    print('Almond Duo local service ready',flush=True)
    def shutdown(*_):
        store.close()
        threading.Thread(target=server.shutdown,daemon=True).start()
    signal.signal(signal.SIGTERM,shutdown)
    signal.signal(signal.SIGINT,shutdown)
    try:server.serve_forever(poll_interval=.2)
    finally:store.close();server.server_close()
    return 0


if __name__=='__main__':sys.exit(main())
