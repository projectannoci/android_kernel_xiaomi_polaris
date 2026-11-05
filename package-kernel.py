#!/usr/bin/env python3
"""Package the source-built kernel together with its matching appended DTBs."""
from pathlib import Path
import argparse, stat, zipfile, zlib

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('profile', choices=['raw','baseline'])
parser.add_argument('--payload', type=Path, default=root/'out/arch/arm64/boot/Image.gz-dtb')
args = parser.parse_args()
payload = args.payload.read_bytes()
decoder = zlib.decompressobj(31)
image = decoder.decompress(payload)+decoder.flush()
assert image[56:60] == b'ARM\x64'
assert decoder.unused_data[:4] == b'\xd0\x0d\xfe\xed', 'Paired DTBs required'
start = image.index(b'IKCFG_ST')+8
end = image.index(b'IKCFG_ED',start)
config = root/('CONFIG.final' if args.profile=='raw' else 'CONFIG.baseline')
assert zlib.decompress(image[start:end],31) == config.read_bytes()
name = 'Gaming_1_KSUN' if args.profile=='raw' else 'BASELINE_R2_DTB'
dest = root/'deliverables'/f'Singularity_v1_ProjectNoci_polaris_{name}.zip'
dest.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
    for p in sorted((root/'anykernel').rglob('*')):
        rel = p.relative_to(root/'anykernel')
        if not p.is_file() or '.git' in rel.parts or p.name=='placeholder': continue
        if rel.parts[0].startswith('Image') or str(rel)=='README.md': continue
        out.write(p,rel.as_posix())
    info = zipfile.ZipInfo('Image.gz-dtb')
    info.external_attr = (stat.S_IFREG|0o644)<<16
    info.compress_type = zipfile.ZIP_DEFLATED
    out.writestr(info,payload)
    notes = (root/'BUILD.txt').read_bytes() if args.profile=='raw' else (
        b'Singularity v1 @ProjectNoci / BASELINE R2\n'
        b'Polaris AOSP Android 13+ / downstream Linux 4.9\n'
        b'No built-in KernelSU. Existing Magisk ramdisk is retained.\n'
        b'No RAW bandwidth policy. CPU performance, GPU msm-adreno-tz.\n'
        b'Kernel + matching source-built DTBs are installed together.\n'
        b'Existing ROM ramdisk/cmdline/boot metadata retained.\n'
        b'Diagnostic alternative to RAW. Physical boot not yet verified.\n')
    out.writestr('BUILD.txt',notes)
    assert out.testzip() is None
print(dest)
