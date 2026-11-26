"""Size of the key class of a trail WITHOUT the independence assumption: approximate model counting (ApproxMC) of the master
keys K for which both K and its partner (K ^ dK, or ROL_g(K) ^ dK in RX mode) produce the round-key differences of the trail
under the real v3 key schedule.   python3 count_class.py results/<trails>.jsonl [epsilon=0.3] [delta=0.05] [seed=20261126]
Output: model prediction 64 - w_key against log2 of the counted class (count is within a factor 1+epsilon with prob. 1-delta)."""
import sys, json, math, time, pyapproxmc
from trail_search import Mo
from simon_ks import const
N=16
f=sys.argv[1]; EPS=float(sys.argv[2]) if len(sys.argv)>2 else 0.3; DEL=float(sys.argv[3]) if len(sys.argv)>3 else 0.05; SEED=int(sys.argv[4]) if len(sys.argv)>4 else 20261126
def schedule(m,k,i):
    """clauses forcing word list k (signed literals) to satisfy the v3 step for round key i"""
    k0,k1,k3=k[i-4],k[i-3],k[i-1]; a=[]; t=[]
    for j in range(N): o=m.new(); m.AND(o,k3[(j-1)%N],k3[(j-8)%N]); a.append(o)
    for j in range(N): o=m.new(); m.xor([o,k3[(j+3)%N],k1[j],a[j]]); t.append(o)
    c=const(i)
    for j in range(N): m.xor([k[i][j],k0[j],t[j],t[(j+1)%N]],(c>>j)&1)
print("file %s  epsilon %.2f delta %.2f seed %d"%(f,EPS,DEL,SEED)); print("kind mode R | w_data | model: 64-w_key | counted log2(class) | model w_key -> counted w_key | sec")
for line in open(f):
    t=json.loads(line)
    if t['kind']!='v3': continue
    R,g,rx=t['R'],t.get('gamma',0),t['mode']=='rx'; m=Mo(); K=[m.new(N) for _ in range(R)]
    K2=[[(K[i][(j-g)%N] if rx else K[i][j])*(-1 if (t['K'][i]>>j)&1 else 1) for j in range(N)] for i in range(R)]
    for i in range(4,R): schedule(m,K,i); schedule(m,K2,i)
    c=pyapproxmc.Counter(seed=SEED,epsilon=EPS,delta=DEL)
    for cl in m.cl: c.add_clause(cl)
    t0=time.time(); cells,hashes=c.count([v for k in K[:4] for v in k]); lg=(math.log2(cells)+hashes) if cells else float('-inf')
    print("%-3s %-3s %2d | %2d | %2d | %.2f | %2d -> %.2f | %.0f"%(t['kind'],t['mode'],R,t['w_data'],64-t['w_key'],lg,t['w_key'],64-lg,time.time()-t0),flush=True)
