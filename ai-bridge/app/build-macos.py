#!/usr/bin/env python3
"""Package a local Mac .app with a committed project snapshot. No downloads."""
from pathlib import Path
import argparse,json,plistlib,shutil,subprocess,sys,tempfile

p=argparse.ArgumentParser();p.add_argument('destination');args=p.parse_args()
repo=Path(__file__).resolve().parents[2]
dest=Path(args.destination).resolve()
if dest.exists():raise SystemExit('Choose a new destination; the app already exists')
resources=dest/'Contents/Resources';binary=dest/'Contents/MacOS'
resources.mkdir(parents=True);binary.mkdir()
subprocess.run(['git','clone','--quiet','--no-hardlinks',str(repo),str(resources/'project')],check=True)
subprocess.run(['git','remote','remove','origin'],cwd=resources/'project',check=True)
(resources/'runtime.json').write_text(json.dumps({'python':sys.executable}))
subprocess.run(['swiftc',str(repo/'ai-bridge/app/AlmondDuo.swift'),'-o',str(binary/'AlmondDuo'),'-framework','Cocoa','-framework','WebKit'],check=True)
# Reuse the supplied official mark without redrawing it.
with tempfile.TemporaryDirectory() as temp:
    iconset=Path(temp)/'AlmondDuo.iconset';iconset.mkdir()
    source=repo/'branding/logo/png/almond-mark-512.png'
    for size in (16,32,128,256,512):
        for scale in (1,2):
            suffix='@2x' if scale==2 else ''
            subprocess.run(['sips','-z',str(size*scale),str(size*scale),str(source),'--out',str(iconset/('icon_%dx%d%s.png'%(size,size,suffix)))],check=True,stdout=subprocess.DEVNULL)
    subprocess.run(['iconutil','-c','icns',str(iconset),'-o',str(resources/'AlmondDuo.icns')],check=True)
info=dict(CFBundleIconFile='AlmondDuo',CFBundleName='Almond Duo',CFBundleDisplayName='Almond Duo',CFBundleIdentifier='org.almondlinux.duo.local',
          CFBundleExecutable='AlmondDuo',CFBundlePackageType='APPL',CFBundleShortVersionString='0.1',CFBundleVersion='1',
          LSMinimumSystemVersion='12.0',NSHighResolutionCapable=True,NSAppTransportSecurity={'NSAllowsLocalNetworking':True})
with (dest/'Contents/Info.plist').open('wb') as f:plistlib.dump(info,f)
subprocess.run(['codesign','--force','--deep','--sign','-',str(dest)],check=True)
print(dest)
