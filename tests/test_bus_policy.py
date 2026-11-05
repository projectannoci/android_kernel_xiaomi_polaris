from pathlib import Path
import re,subprocess,tempfile
root=Path(__file__).resolve().parents[1]
s=(root/'kernel/drivers/devfreq/governor_bw_hwmon.c').read_text()
scale=int(re.search(r'node->up_scale = (\d+);',s).group(1))
body=re.search(r'\tif \(node->wake == UP_WAKE\) \{.*?\n\t\}\n\n\thyst_lo_tol',s,re.S).group().rsplit('\n\n',1)[0]
c='''#include <assert.h>
#define UP_WAKE 1
#define min(a,b) ((a)<(b)?(a):(b))
struct node {unsigned long prev_req,hist_max_mbps;unsigned int up_scale,wake;};
unsigned long vote(struct node *node, unsigned long meas_mbps, unsigned long meas_mbps_zone) {
 unsigned long req_mbps=meas_mbps;
'''+body+'''
 return req_mbps;
}
int main(void) {
 struct node n={.prev_req=400,.hist_max_mbps=2000,.up_scale=SCALE,.wake=UP_WAKE};
 assert(vote(&n,800,1200)==1200);
 assert(vote(&n,800,900)==900);
 n.hist_max_mbps=900;assert(vote(&n,800,1200)==900);
 n.prev_req=1200;assert(vote(&n,800,1200)==800);
 n.prev_req=400;n.wake=0;assert(vote(&n,800,1200)==800);
 n.wake=UP_WAKE;n.prev_req=800;assert(vote(&n,800,1200)==800);
 return 0;
}
'''.replace('SCALE',str(scale))
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(c);subprocess.run(['gcc','-Wall','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True);subprocess.run([str(p/'test')],check=True)
print('PASS: bus rise headroom, historic peak cap, zone cap, steady/falling traffic')
