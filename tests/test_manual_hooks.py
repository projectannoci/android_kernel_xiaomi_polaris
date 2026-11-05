from pathlib import Path
import re
r=Path(__file__).resolve().parents[1]/'kernel'
# These calls must exist in the active kernel functions, rather than only in the root driver.
checks=[('fs/exec.c',r'ksu_handle_execveat\(&fd, &filename, &argv, &envp, &flags\)'),('fs/read_write.c',r'ksu_handle_vfs_read\(&file, &buf, &count, &pos\)'),('fs/open.c',r'ksu_handle_faccessat\(&dfd, &filename, &mode, NULL\)'),('fs/stat.c',r'ksu_handle_stat\(&dfd, &filename, &flag\)'),('drivers/input/input.c',r'ksu_handle_input_handle_event\(&type, &code, &value\)')]
for f,pat in checks:assert re.search(pat,(r/f).read_text()),f
print('PASS: all five static root hook sites connected')

import subprocess,shutil
od=shutil.which('llvm-objdump')
for f,pat in checks:
 obj=r.parent/'out'/Path(f).with_suffix('.o')
 if obj.exists():
  symbol=re.search(r'(ksu_handle_\w+)',pat).group(1)
  dis=subprocess.check_output([od,'-dr',str(obj)],text=True)
  assert re.search(r'R_AARCH64_CALL26\s+'+symbol,dis),symbol
print('PASS: static hooks present in compiled callsite relocations when build objects are available')
