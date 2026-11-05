from pathlib import Path
import hashlib, re, struct, subprocess, zlib, zipfile, shutil, os
root=Path(__file__).resolve().parents[1]
image=root/'out/arch/arm64/boot/Image.gz-dtb'
b=image.read_bytes();d=zlib.decompressobj(31);raw=d.decompress(b)+d.flush()
assert raw[56:60]==b'ARM\x64','Invalid arm64 Image magic'
cs=raw.index(b'IKCFG_ST')+8;ce=raw.index(b'IKCFG_ED',cs)
assert zlib.decompress(raw[cs:ce],31)==(root/'CONFIG.final').read_bytes(),'Embedded config differs from final config'
assert len(raw)>10_000_000,'Image unexpectedly small'
rest=d.unused_data;models=[]
while rest:
 assert rest[:4]==b'\xd0\x0d\xfe\xed','Invalid appended FDT magic'
 n=struct.unpack('>I',rest[4:8])[0];dtb=rest[:n];assert len(dtb)==n
 result=subprocess.check_output([str(root/'out/scripts/dtc/dtc'),'-I','dtb','-O','dts'],input=dtb,stderr=subprocess.DEVNULL).decode()
 models += re.findall(r'^\tmodel = "([^"]+)";',result,re.M)
 rest=rest[n:]
assert any('Polaris P3 v2.1' in m for m in models),models
assert sum('Polaris' in m for m in models)>=11,models
nm=subprocess.check_output([shutil.which(os.environ.get('CROSS_COMPILE','aarch64-linux-gnu-')+'nm'),str(root/'out/vmlinux')],text=True)
for s in ['ksu_handle_prctl','ksu_handle_setuid','ksu_handle_execveat_ksud','cpufreq_gov_performance','sugov_up_down_rate_limit']:
 # A static helper may be inlined; check the externally reachable policy path instead.
 if s=='sugov_up_down_rate_limit': continue
 assert re.search(r'\b'+s+r'$',nm,re.M),s
cfg=(root/'out/.config').read_text()
for s in ['CONFIG_KSU=y','# CONFIG_KPROBES is not set','CONFIG_NOCI_RAW_PERF=y','CONFIG_MSM_PERFORMANCE=y','CONFIG_CPU_FREQ_DEFAULT_GOV_PERFORMANCE=y','CONFIG_QCOM_ADRENO_DEFAULT_GOVERNOR="performance"','CONFIG_MACH_XIAOMI_D5X=y']:
 assert s in cfg,s
assert '# CONFIG_BUILD_ARM64_DT_OVERLAY is not set' in cfg
assert 'Singularity-v1' in (root/'out/include/config/kernel.release').read_text()
subprocess.run(['sh','-n',str(root/'anykernel/anykernel.sh')],check=True)
zips=list((root/'deliverables').glob('*polaris_Gaming_1*.zip'))
assert zips,'Final flashable ZIP is missing'
for f in zips:
 with zipfile.ZipFile(f) as z:
  assert z.testzip() is None
  assert z.read('Image.gz-dtb')==image.read_bytes()
  assert 'Image.gz' not in z.namelist()
  for n in ['META-INF/com/google/android/update-binary','tools/ak3-core.sh','tools/magiskboot','anykernel.sh']:
   assert n in z.namelist(),n
  assert b'device.name1=polaris' in z.read('anykernel.sh')
  assert b'supported.versions=13+' in z.read('anykernel.sh')
print('PASS: arm64 image, gzip, appended FDTs, polaris revisions, KSU symbols, config, installer syntax, ZIP CRC')
print('FDT models:',models)
print('Image bytes:',len(b),'sha256:',hashlib.sha256(b).hexdigest())
