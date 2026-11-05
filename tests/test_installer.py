from pathlib import Path
import tempfile, subprocess, re, os
root=Path(__file__).resolve().parents[1]
up=(root/'anykernel/META-INF/com/google/android/update-binary').read_text()
def fn(name):
 m=re.search(r'^'+name+r'\(\) \{\n.*?^\}',up,re.S|re.M)
 assert m,name
 return m.group()
functions='\n'.join(fn(x) for x in ['int2ver','do_versioncheck'])
# Real updater function; only filesystem/property access and abort output are stubbed.
with tempfile.TemporaryDirectory() as td:
 p=Path(td); (p/'anykernel.sh').write_bytes((root/'anykernel/anykernel.sh').read_bytes())
 script='''
file_getprop() { grep "^$2=" "$1" 2>/dev/null | tail -n1 | cut -d= -f2-; }
ui_print() { printf '%s\\n' "$*"; }
abort() { printf '%s\\n' "$*"; exit 1; }
'''+functions+'''
file_getprop() {
 local propfile="$1";
 case "$propfile" in /system/*|/system_root/*|/product/*|/system_ext/*) propfile="$FIXTURE_ROOT$propfile";; esac;
 grep "^$2=" "$propfile" 2>/dev/null | tail -n1 | cut -d= -f2-;
}
if [ -f "$COMPAT_SCRIPT" ]; then . "$COMPAT_SCRIPT"; fi
noci_system_prop_files() { printf '%s\\n' "$FIXTURE_ROOT/system/build.prop" "$FIXTURE_ROOT/system_root/system/build.prop" "$FIXTURE_ROOT/system/system/build.prop"; }
BOOTMODE=false;
getprop() { case "$1" in ro.build.version.sdk) echo 28;; ro.build.version.release) echo 9;; esac; }
do_versioncheck
'''
 cases=[('A13',33,'system/build.prop',True),('A14',34,'system/build.prop',True),('SAR A13',33,'system_root/system/build.prop',True),('SAR A14',34,'system_root/system/build.prop',True),('A12',32,'system/build.prop',False),('missing target props',None,None,False)]
 errors=[]
 for name,sdk,path,expected in cases:
  for f in p.rglob('build.prop'): f.unlink()
  if path:
   f=p/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(f'ro.build.version.sdk={sdk}\nro.build.version.release={sdk-20}\n')
  env=dict(os.environ,FIXTURE_ROOT=str(p),AKHOME=str(root/'anykernel'),COMPAT_SCRIPT=str(root/'anykernel/tools/noci-compat.sh'))
  r=subprocess.run(['bash','-c',script],cwd=p,env=env,capture_output=True,text=True)
  passed=r.returncode==0
  if passed!=expected:errors.append((name,r.stdout,r.stderr))
  print(('PASS' if passed==expected else 'FAIL'),name)
 assert not errors,errors
