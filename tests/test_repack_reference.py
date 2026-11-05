from pathlib import Path
import os,subprocess,shutil,struct,tempfile
root=Path(__file__).resolve().parents[1];outer=root.parent
qemu=Path(os.environ.get('QEMU_ARM',str(outer/'final_tools/usr/bin/qemu-arm-static')));mb=root/'anykernel/tools/magiskboot'
fixture=Path(tempfile.mkdtemp(prefix='r2-repack-',dir=outer))
(fixture/'tools').mkdir()
shutil.copy2(root/'anykernel/anykernel.sh',fixture/'anykernel.sh')
shutil.copy2(root/'anykernel/tools/noci-compat.sh',fixture/'tools/noci-compat.sh')
payload=Path(os.environ.get('PAYLOAD_GZ',str(root/'out/arch/arm64/boot/Image.gz-dtb')))
shutil.copy2(payload,fixture/'Image.gz-dtb')
(fixture/'tools/actual-core.sh').write_text((root/'anykernel/tools/ak3-core.sh').read_text().rsplit('setup_ak;',1)[0])
(fixture/'tools/ak3-core.sh').write_text('''. "$AKHOME/tools/actual-core.sh"
BLOCK="$REFERENCE_BOOT"
CUSTOMDD=bs=1048576
ui_print() { printf '%s\\n' "$*"; }
abort() { printf '%s\\n' "$*" >&2; exit 1; }
magiskboot() {
 "$QEMU" "$MAGISKBOOT" "$@"
 local result=$?
 # The host lacks recovery root's DAC override for Magisk's mode-000 config.
 [ ! -f .magisk ] || chmod u+r .magisk
 return "$result"
}
blockdev() { :; }
dd() {
 case "$*" in *"of=$BLOCK"*) printf '%s\\n' "$*" >> "$AKHOME/write-intent.log";;
 *) command dd "$@";; esac
}
''')
ref=Path(os.environ.get('POLARIS_BOOT',str(outer/'upload/boot.emmc.win')));ref_bytes=ref.read_bytes()
env=dict(os.environ,AKHOME=str(fixture),QEMU=str(qemu),MAGISKBOOT=str(mb),REFERENCE_BOOT=str(ref),NOCI_ANDROID_SDK='34',NOCI_ANDROID_RELEASE='14')
r=subprocess.run(['bash','anykernel.sh'],cwd=fixture,env=env,capture_output=True,text=True)
(fixture/'install.log').write_text(r.stdout+r.stderr)
assert r.returncode==0,r.stdout+r.stderr
assert ref.read_bytes()==ref_bytes,'Reference boot was modified'
assert len((fixture/'write-intent.log').read_text().splitlines())==2
new=fixture/'boot-new.img';assert new.stat().st_size<=len(ref_bytes)
after=fixture/'after';after.mkdir();r=subprocess.run([str(qemu),str(mb),'unpack','-h',str(new)],cwd=after,capture_output=True,text=True);assert r.returncode==0,r.stderr
(fixture/'unpack.log').write_text(r.stdout+r.stderr)
import zlib
decoder=zlib.decompressobj(31)
expected=decoder.decompress(payload.read_bytes())+decoder.flush()
paired_dtbs=decoder.unused_data
assert paired_dtbs[:4]==b'\xd0\x0d\xfe\xed'
actual=(after/'kernel').read_bytes()
assert actual in [expected,expected.replace(b'skip_initramfs',b'want_initramfs')],'Wrong final kernel'
print('Kernel Magisk compatibility substitution:',actual!=expected)
for name in ['ramdisk.cpio','header']:
 assert (fixture/'split_img'/name).read_bytes()==(after/name).read_bytes(),name
assert (after/'kernel_dtb').read_bytes()==paired_dtbs,'Repack retained incompatible old DTBs'
page_size=struct.unpack_from('<I',ref_bytes,36)[0]
kernel_size=struct.unpack_from('<I',ref_bytes,8)[0]
original=zlib.decompressobj(31)
original.decompress(ref_bytes[page_size:page_size+kernel_size]);original.flush()
assert paired_dtbs!=original.unused_data,'Expected the incompatible reference DTBs to be replaced'
newb=new.read_bytes()
# Boot v1: payload sizes and SHA1 change; addresses and boot metadata must stay.
for start,end in [(0,8),(12,16),(20,576),(608,1648)]:assert ref_bytes[start:end]==newb[start:end],(start,end)
def avb_flags(b):
 if b[-64:-60]!=b'AVBf':return None
 off=struct.unpack('>Q',b[-44:-36])[0]
 assert b[off:off+4]==b'AVB0'
 return struct.unpack('>I',b[off+120:off+124])[0]
assert avb_flags(ref_bytes)==avb_flags(newb),'AVB flags changed'
print('PASS: actual AnyKernel split/repack via packaged ARM magiskboot; all partition writes stubbed')
print('PASS: final kernel + DTBs match the paired build; ramdisk, cmdline/header, OS version and AVB flags preserved')
print('boot bytes',new.stat().st_size,'partition bytes',len(ref_bytes),'AVB flags',avb_flags(newb))
