#!/usr/bin/env python3
"""Keep the source-built DTB order of the boot-confirmed Polaris R2 package."""
from pathlib import Path
from collections import Counter
import struct,zlib

root=Path(__file__).resolve().parent
out=root/'out/arch/arm64/boot'
payload=out/'Image.gz-dtb'
decoder=zlib.decompressobj(31)
decoder.decompress(payload.read_bytes());decoder.flush()
rest=decoder.unused_data
original=[]
while rest:
    assert rest[:4]==b'\xd0\x0d\xfe\xed'
    size=struct.unpack('>I',rest[4:8])[0]
    assert 40<=size<=len(rest)
    original.append(rest[:size]);rest=rest[size:]
names=(root/'DTB_ORDER.txt').read_text().splitlines()
assert len(names)==len(set(names))
assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in names)
ordered=[(out/'dts'/name).read_bytes() for name in names]
assert Counter(original)==Counter(ordered),'Compiled DTBs differ from the expected board set'
payload.write_bytes((out/'Image.gz').read_bytes()+b''.join(ordered))
print('Paired',len(ordered),'compiled DTBs in the boot-confirmed board order')
