"""Local desktop-app protocol and job-store boundaries (no model calls)."""
import http.client
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest import mock
from http.server import ThreadingHTTPServer

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('almond_app',ROOT/'ai-bridge/app/server.py')
app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)


class AppHTTP(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        with mock.patch.object(app.Store,'check_connections'):
            self.store=app.Store(self.temp.name,ROOT)
        self.http=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        self.http.store=self.store;self.http.token='test-only-token'
        self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start()

    def tearDown(self):
        self.http.shutdown();self.http.server_close();self.temp.cleanup()

    def request(self,method,path,body=None,**headers):
        data=json.dumps(body) if body is not None else None
        headers.setdefault('X-Almond-Token',self.http.token)
        conn=http.client.HTTPConnection('127.0.0.1',self.http.server_port)
        conn.request(method,path,data,headers)
        response=conn.getresponse();result=response.read();conn.close()
        return response.status,json.loads(result)

    def test_state_requires_token(self):
        code,_=self.request('GET','/api/state',**{'X-Almond-Token':'wrong'})
        self.assertEqual(code,403)
        code,data=self.request('GET','/api/state')
        self.assertEqual(code,200);self.assertEqual(data['project'],'Almond Linux')

    def test_foreign_origin_cannot_start(self):
        code,_=self.request('POST','/api/jobs',{'prompt':'hello','mode':'ask'},Origin='https://example.invalid')
        self.assertEqual(code,403);self.assertEqual(self.store.jobs(),[])

    def test_foreign_host_rejected(self):
        self.assertEqual(self.request('GET','/api/state',Host='evil.invalid')[0],403)

    def test_invalid_payload_is_error(self):
        for value in [[],{'prompt':'','mode':'ask'},{'prompt':'hello','mode':'invalid'}]:
            self.assertEqual(self.request('POST','/api/jobs',value)[0],400)

    def test_sign_in_required_before_launch(self):
        self.assertEqual(self.request('POST','/api/jobs',{'prompt':'hi','mode':'ask'})[0],409)
        self.assertEqual(self.store.jobs(),[])

    def test_paths_cannot_escape_job_store(self):
        with self.assertRaises(ValueError):self.store.job_dir('../../outside')
        self.assertEqual(self.request('GET','/api/jobs/../../outside')[0],404)

    def test_active_job_prevents_duplicate(self):
        key='a'*32;folder=self.store.job_dir(key);folder.mkdir()
        app.atomic_json(folder/'job.json',dict(id=key,status='running',created=time.time()))
        self.store.connections={who:{'authenticated':True} for who in ('claude','codex')}
        with self.assertRaisesRegex(RuntimeError,'already running'):
            self.store.start('next','ask')

    def test_truncated_event_does_not_break_polling(self):
        key='b'*32;folder=self.store.job_dir(key);folder.mkdir()
        app.atomic_json(folder/'job.json',dict(id=key,status='completed',created=time.time()))
        (folder/'messages.jsonl').write_text('{"body":"complete"}\n{"body":')
        self.assertEqual(self.store.detail(key)['messages'],[{'body':'complete'}])

    def test_restart_marks_unfinished_run_interrupted(self):
        key='c'*32;folder=self.store.job_dir(key);folder.mkdir()
        app.atomic_json(folder/'job.json',dict(id=key,status='running',created=time.time()))
        with mock.patch.object(app.Store,'check_connections'):
            fresh=app.Store(self.temp.name,ROOT)
        self.assertEqual(fresh.jobs()[0]['status'],'interrupted')


if __name__=='__main__':unittest.main()
