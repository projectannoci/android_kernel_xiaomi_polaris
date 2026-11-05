from pathlib import Path
import re,subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=(root/'kernel/drivers/cpufreq/cpu-boost.c').read_text()
fn=re.search(r'static int boost_adjust_notify\(.*?\n\}',source,re.S).group()
header=(root/'kernel/include/linux/cpufreq.h').read_text()
verify=re.search(r'static inline void cpufreq_verify_within_limits\(.*?\n\}',header,re.S).group()
c='''#include <assert.h>
#include <limits.h>
#define CONFIG_NOCI_RAW_PERF 1
#define CPUFREQ_ADJUST 1
#define NOTIFY_OK 0
#define pr_debug(...) do {} while(0)
#define min(a,b) ((a)<(b)?(a):(b))
struct notifier_block {int unused;};
struct cpufreq_policy {unsigned int cpu,min,max;};
struct cpu_sync {unsigned int input_boost_min;};
static struct cpu_sync sync_info[8];
#define per_cpu(name,cpu) name[cpu]
'''+verify+'\n'+fn+'''
int main(void) {
 struct cpufreq_policy p={.cpu=4,.min=300000,.max=1209600};
 sync_info[4].input_boost_min=2803200;
 boost_adjust_notify(0,CPUFREQ_ADJUST,&p);
 assert(p.min==1209600 && p.max==1209600);
 p.min=300000;p.max=2803200;sync_info[4].input_boost_min=2400000;
 boost_adjust_notify(0,CPUFREQ_ADJUST,&p);
 assert(p.min==2400000 && p.max==2803200);
 p.min=300000;sync_info[4].input_boost_min=0;
 boost_adjust_notify(0,CPUFREQ_ADJUST,&p);
 assert(p.min==300000 && p.max==2803200);
 return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'t.c').write_text(c)
 subprocess.run(['gcc','-Wall','-Werror',str(p/'t.c'),'-o',str(p/'t')],check=True)
 subprocess.run([str(p/'t')],check=True)
print('PASS: input boost reaches requested floor, respects policy cap, and ignores an inactive boost')
