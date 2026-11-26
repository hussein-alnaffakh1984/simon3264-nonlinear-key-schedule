"""Synthesize each module with Yosys (WASM build) to generic gates and compute a NAND2-equivalent estimate.
GE factors are ASSUMPTIONS (typical standard-cell ratios), not taken from a real library."""
import subprocess, re, json, sys
GE = {'NOT':0.67,'NAND':1.00,'NOR':1.00,'AND':1.33,'OR':1.33,'XOR':2.67,'XNOR':2.67,'MUX':2.33,'DFF':5.33,'SDFF':6.67}
mods = [('ks_round_std','rtl/ks_round.v'),('ks_round_v2','rtl/ks_round.v'),('ks_round_v3','rtl/ks_round_v3.v'),('ks_serial_std','rtl/ks_round.v rtl/ks_serial_std.v'),('ks_serial_v3','rtl/ks_round_v3.v rtl/ks_serial_v3.v')]
rows = []
for top, files in mods:
    scr = f"read_verilog {files}; synth -flatten -top {top}; abc -g AND,NAND,OR,NOR,XOR,XNOR,MUX; opt_clean; ltp -noff; tee -o rtl/{top}.stat.json stat -json; write_verilog -noattr rtl/{top}.net.v"
    r = subprocess.run(['yowasp-yosys','-q','-l',f'rtl/{top}.log','-p',scr], capture_output=True, text=True)
    if r.returncode: print(r.stdout[-2000:], r.stderr[-2000:]); sys.exit(1)
    log = open(f'rtl/{top}.log').read()
    m = re.search(r'Longest topological path in .* \(length=(\d+)\)', log); depth = int(m.group(1)) if m else None
    cells = json.load(open(f'rtl/{top}.stat.json'))['modules']['\\'+top]['num_cells_by_type']
    c = {}
    for k, v in cells.items():
        name = k.strip('$_'); name = {'DFF_P':'DFF','SDFF_PP0':'SDFF'}.get(name, name)
        if name == 'scopeinfo': continue          # bookkeeping pseudo-cell, not hardware
        c[name] = c.get(name, 0) + int(v)
    unknown = [k for k in c if k not in GE]
    ge = sum(GE[k]*v for k, v in c.items() if k in GE)
    rows.append((top, c, ge, depth, unknown))
keys = ['NOT','NAND','NOR','AND','OR','XOR','XNOR','MUX','DFF','SDFF']
print('GE factors assumed:', GE)
print('| module | ' + ' | '.join(keys) + ' | cells | logic depth (gates) | GE (assumed factors) |')
print('|---|' + '---:|'*(len(keys)+3))
for top, c, ge, depth, unk in rows:
    print(f'| {top} | ' + ' | '.join(str(c.get(k,0)) for k in keys) + f' | {sum(c.values())} | {depth} | {ge:.1f} |' + (f' UNKNOWN {unk}' if unk else ''))
