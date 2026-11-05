from pathlib import Path
import tempfile,subprocess,os,re,gzip,struct
root=Path(__file__).resolve().parents[1];ak=root/'anykernel'
up=(ak/'META-INF/com/google/android/update-binary').read_text()
def fn(name):return re.search(r'^'+name+r'\(\) \{\n.*?^\}',up,re.S|re.M).group()
raw=bytearray(8*1024*1024);raw[56:60]=b'ARM\x64';raw[128:200]=b'Linux version 4.9.337-Singularity-v1 (ProjectNoci@Singularity) #1 SMP\0'.ljust(72,b'\0')
dtb=(root/'out/arch/arm64/boot/dts/qcom/polaris-mp-v2.1.dtb').read_bytes()
with tempfile.TemporaryDirectory() as d:
 base=Path(d)
 cases={'valid':True,'wrong_device':False,'missing_payload':False,'bad_gzip':False,'bad_arm64':False,'missing_paired_dtb':False,'bad_paired_dtb':False,'old_family':False,'bad_header':False,'bad_format':False,'missing_dtb':False,'oversize':False,'repack_fail':False}
 for case,expected in cases.items():
  p=base/case;(p/'tools').mkdir(parents=True)
  (p/'anykernel.sh').write_bytes((ak/'anykernel.sh').read_bytes())
  (p/'tools/noci-compat.sh').write_bytes((ak/'tools/noci-compat.sh').read_bytes())
  (p/'tools/actual-core.sh').write_text((ak/'tools/ak3-core.sh').read_text().rsplit('setup_ak;',1)[0])
  if case!='missing_payload':
   b=bytes(raw)
   if case=='bad_arm64':b=b[:56]+b'FAIL'+b[60:]
   paired=b'' if case=='missing_paired_dtb' else (b'BADTREE' if case=='bad_paired_dtb' else dtb)
   (p/'Image.gz-dtb').write_bytes((b'broken' if case=='bad_gzip' else gzip.compress(b))+paired)
  boot=bytearray(4096);boot[:8]=b'INVALID!' if case=='bad_format' else b'ANDROID!';struct.pack_into('<I',boot,40,3 if case=='bad_header' else 1)
  (p/'reference.img').write_bytes(boot)
  (p/'split_img').mkdir();(p/'split_img/kernel').write_bytes(b'Linux version '+(b'4.19.325' if case=='old_family' else b'4.9.337')+b'-perf (builder@host) #1 SMP\0')
  if case!='missing_dtb':(p/'split_img/kernel_dtb').write_bytes(b'ORIGINAL_DTB')
  (p/'split_img/ramdisk.cpio').write_bytes(b'ORIGINAL_RAMDISK')
  stub='''. "$AKHOME/tools/actual-core.sh"
ui_print() { :; }
abort() { printf '%s\\n' "$*" >&2; exit 1; }
split_boot() { cp "$AKHOME/reference.img" "$BOOTIMG"; BLOCK="$AKHOME/block"; CUSTOMDD=bs=4096; }
blockdev() { :; }
dd() { printf '%s\\n' "$*" >> "$AKHOME/write.log"; }
magiskboot() {
 case "$1" in
 split|dtb) "$QEMU" "$MAGISKBOOT" "$@"; return $?;;
 cpio) return 0;;
 repack)
  [ "$CASE" = repack_fail ] && return 1
  if [ "$CASE" = oversize ]; then truncate -s 8192 "$3"; else truncate -s 2048 "$3"; fi
  return 0;;
 *) return 1;;
 esac
}
'''
  (p/'tools/ak3-core.sh').write_text(stub)
  script='''
file_getprop() { grep "^$2=" "$1" 2>/dev/null | tail -n1 | cut -d= -f2-; }
ui_print() { :; }
abort() { printf '%s\\n' "$*" >&2; exit 1; }
getprop() { if [ "$1" = ro.product.device ]; then if [ "$CASE" = wrong_device ]; then echo beryllium; else echo polaris; fi; fi; }
'''+fn('do_devicecheck')+'''
do_devicecheck
. ./anykernel.sh
'''
  env=dict(os.environ,AKHOME=str(p),NOCI_ANDROID_SDK='34',NOCI_ANDROID_RELEASE='14',CASE=case,NO_MAGISK_CHECK='1',QEMU=os.environ.get('QEMU_ARM',str(root.parent/'final_tools/usr/bin/qemu-arm-static')),MAGISKBOOT=str(ak/'tools/magiskboot'))
  r=subprocess.run(['bash','-c',script],cwd=p,env=env,capture_output=True,text=True)
  assert (p/'split_img/ramdisk.cpio').read_bytes()==b'ORIGINAL_RAMDISK'
  if case not in ['missing_dtb','valid','oversize','repack_fail']:assert (p/'split_img/kernel_dtb').read_bytes()==b'ORIGINAL_DTB'
  writes=(p/'write.log').read_text().splitlines() if (p/'write.log').exists() else []
  good=r.returncode==0 and len(writes)==2 if expected else r.returncode!=0 and not writes
  print(('PASS' if good else 'FAIL'),case,r.stderr.strip())
  assert good,(case,r.returncode,writes,r.stderr)
