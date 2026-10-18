"""Explicit app integration test with fake agents only. Run from a committed checkout."""
import importlib.util,json,time,tempfile,subprocess
from pathlib import Path
from unittest.mock import patch
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('app',root/'ai-bridge/app/server.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
temporary=tempfile.TemporaryDirectory(prefix='almond-app-test-')
state=Path(temporary.name)
app.ENV.update(ALMOND_DUO_CLAUDE=str(root/'ai-bridge/tests/fakes/fake_claude'),ALMOND_DUO_CODEX=str(root/'ai-bridge/tests/fakes/fake_codex'),FAKE_AI_STATE=str(state/'fake'))
with patch.object(app.Store,'check_connections'):store=app.Store(state,root)
store.connections={x:{'authenticated':True} for x in ('claude','codex')}
def run(mode,parent=None):
 k=store.start('Integration test of visible workflow',mode,parent)
 for _ in range(240):
  d=store.detail(k)
  if d['status'] not in app.ACTIVE:break
  time.sleep(.5)
 assert d['status']=='completed',d
 assert not subprocess.check_output(['git','remote'],cwd=d['workspace']).strip()
 print(mode,d['status'],len(d['messages']),flush=True)
 return k,d
k,d=run('ask');assert len(d['messages'])==5
k2,d2=run('ask',k);assert d2['source']==d['workspace']
k3,d3=run('build');assert (Path(d3['workspace'])/'docs/DUO-DEMO.md').exists()
# Launch and immediately stop a real worker process, retaining files.
k4=store.start('Cancellation test','ask');store.stop(k4);assert store.detail(k4)['status']=='stopped'
store.close()
print('All app integration assertions passed',flush=True)
temporary.cleanup()
