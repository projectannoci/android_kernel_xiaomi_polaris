from pathlib import Path
import os, re, struct, subprocess, zlib

root = Path(__file__).resolve().parents[1]
payload = Path(os.environ.get('PAYLOAD', root/'out/arch/arm64/boot/Image.gz-dtb'))
decoder = zlib.decompressobj(31)
decoder.decompress(payload.read_bytes()); decoder.flush()
dtbs = Path(os.environ['DTB_PATH']).read_bytes() if 'DTB_PATH' in os.environ else decoder.unused_data
source = (root/'kernel/drivers/clk/qcom/gpucc-sdm845.c').read_text()
tables = {}
for suffix in ['', '_sdm845_v2']:
    block = re.search(r'ftbl_gpu_cc_gx_gfx3d_clk_src'+suffix+r'\[\] = \{(.*?)\n\};', source, re.S).group(1)
    tables[suffix] = {int(x) for x in re.findall(r'F\((\d+),', block)}
count = 0
while dtbs:
    assert dtbs[:4] == b'\xd0\x0d\xfe\xed', 'Malformed DTB stream'
    size = struct.unpack('>I',dtbs[4:8])[0]
    assert 40 <= size <= len(dtbs)
    dtb, dtbs = dtbs[:size], dtbs[size:]
    text = subprocess.check_output([str(root/'out/scripts/dtc/dtc'),'-I','dtb','-O','dts'],input=dtb,stderr=subprocess.DEVNULL).decode()
    model = re.search(r'\bmodel = "([^"]+)";',text).group(1)
    if 'polaris' not in model.lower(): continue
    count += 1
    rates = {int(x,16) for x in re.findall(r'qcom,gpu-freq = <(0x[0-9a-f]+)>;',text)} - {0}
    expected = tables['_sdm845_v2' if 'v2' in model.lower() else '']
    assert rates <= expected, f'{model}: unsupported GPU rates {sorted(rates-expected)}'
assert count >= 11, f'Missing Polaris hardware revisions: {count}'
print(f'PASS: {count} Polaris DTBs have GPU rates supported by the paired clock driver')
