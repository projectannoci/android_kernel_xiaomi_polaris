from pathlib import Path
import concurrent.futures,hashlib,subprocess,urllib.request,time
root=Path(__file__).resolve().parent
cache=root/'final_debs';cache.mkdir(exist_ok=True)
dest=root/'final_tools';dest.mkdir(exist_ok=True)
packages='clang-18 libclang-cpp18 libllvm18 llvm-18 llvm-18-runtime llvm-18-linker-tools libclang-common-18-dev libclang1-18 lld-18 libz3-4 libpfm4 libtinfo6 libzstd1 libxml2 bc bison flex libfl2 libfl-dev libssl-dev libelf-dev gcc-13-aarch64-linux-gnu cpp-13-aarch64-linux-gnu gcc-13-arm-linux-gnueabi cpp-13-arm-linux-gnueabi gcc-13-cross-base gcc-13-aarch64-linux-gnu-base gcc-13-arm-linux-gnueabi-base libgcc-13-dev-arm64-cross libgcc-13-dev-armel-cross libgcc-s1-arm64-cross libgcc-s1-armel-cross binutils-aarch64-linux-gnu binutils-arm-linux-gnueabi libbinutils libctf0 libctf-nobfd0 libsframe1 qemu-user-static cpio zip busybox-static'.split()
def fetch(name):
 text=subprocess.check_output(['apt-cache','show',name],text=True).split('\n\n')[0]
 d=dict(l.split(': ',1) for l in text.splitlines() if ': ' in l)
 path=cache/Path(d['Filename']).name
 for attempt in range(3):
  try:
   if not path.exists() or path.stat().st_size!=int(d['Size']):
    url=(['https://archive.ubuntu.com/ubuntu/','https://security.ubuntu.com/ubuntu/','https://snapshot.ubuntu.com/ubuntu/20260828T000000Z/'][attempt])+d['Filename']
    with urllib.request.urlopen(url,timeout=90) as src,path.open('wb') as out:
     while chunk:=src.read(1024*1024):out.write(chunk)
   assert path.stat().st_size==int(d['Size']),name
   assert hashlib.sha256(path.read_bytes()).hexdigest()==d['SHA256'],name
   return path
  except Exception:
   path.unlink(missing_ok=True)
   if attempt==2:
    print('FAILED PACKAGE',name,d['Filename'],flush=True)
    raise
   time.sleep(1)
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
 paths=list(pool.map(fetch,packages))
print('Verified',len(paths),'packages; extracting sequentially',flush=True)
for p in paths:subprocess.run(['dpkg-deb','-x',str(p),str(dest)],check=True)
for name in ['aarch64-linux-gnu','arm-linux-gnueabi']:
 p=dest/'usr/bin'/f'{name}-gcc'
 if not p.exists():p.symlink_to(f'{name}-gcc-13')
print('Toolchain ready',flush=True)
