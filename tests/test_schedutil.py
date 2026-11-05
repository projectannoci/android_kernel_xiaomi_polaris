from pathlib import Path
import re, subprocess, tempfile
s=Path('kernel/kernel/sched/cpufreq_schedutil.c').read_text()
f=re.search(r'static bool sugov_up_down_rate_limit\(.*?\n\}',s,re.S).group()
defaults={n:int(re.search(r'tunables->'+n+r' = (\d+);',s).group(1)) for n in ['up_rate_limit_us','down_rate_limit_us']}
c='''#include <stdbool.h>
#include <stdint.h>
#include <assert.h>
typedef int64_t s64; typedef uint64_t u64;
struct sugov_policy { s64 last_freq_update_time, up_rate_delay_ns, down_rate_delay_ns; unsigned int next_freq; };
'''+f+'''
int main(void) {
struct sugov_policy p={.last_freq_update_time=0, .next_freq=2000000,
.up_rate_delay_ns=UP_NS, .down_rate_delay_ns=DOWN_NS};
assert(!sugov_up_down_rate_limit(&p,0,2800000));
assert(sugov_up_down_rate_limit(&p,1000000,1000000));
assert(sugov_up_down_rate_limit(&p,19999999,1000000));
assert(!sugov_up_down_rate_limit(&p,20000000,1000000));
p.last_freq_update_time=100000000;
assert(!sugov_up_down_rate_limit(&p,100000001,2800000));
assert(sugov_up_down_rate_limit(&p,119999999,1000000));
return 0;
}
'''
c=c.replace('UP_NS',str(defaults['up_rate_limit_us']*1000)).replace('DOWN_NS',str(defaults['down_rate_limit_us']*1000))
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'t.c').write_text(c)
 subprocess.run(['gcc','-Wall','-Werror',str(p/'t.c'),'-o',str(p/'t')],check=True)
 subprocess.run([str(p/'t')],check=True)
print('PASS: immediate frequency increase; 20ms frequency decrease hysteresis')
