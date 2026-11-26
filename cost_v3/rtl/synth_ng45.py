"""Synthesis to the NanGate 45 nm Open Cell Library (typical corner) with Yosys + ABC.  Area in um^2, GE = area / area(NAND2_X1)."""
import subprocess, re, json, sys
LIB='rtl/ng45.lib'; NAND2=0.798
mods=[('ks_round_std','rtl/ks_round.v'),('ks_round_v3','rtl/ks_round_v3.v'),('ks_serial_std','rtl/ks_round.v rtl/ks_serial_std.v'),('ks_serial_v3','rtl/ks_round_v3.v rtl/ks_serial_v3.v')]
print('| module | cells | area (um^2) | GE (NAND2_X1 = %.3f um^2) | ABC delay (ps) |'%NAND2); print('|---|---:|---:|---:|---:|')
for top,files in mods:
    scr=f"read_verilog {files}; synth -flatten -top {top}; dfflibmap -liberty {LIB}; abc -liberty {LIB}; opt_clean; tee -o rtl/{top}.ng45.json stat -liberty {LIB} -json; write_verilog -noattr rtl/{top}.ng45.v"
    r=subprocess.run(['yowasp-yosys','-l',f'rtl/{top}.ng45.log','-p',scr],capture_output=True,text=True)
    if r.returncode: print(r.stdout[-1500:],r.stderr[-1500:]); sys.exit(1)
    log=open(f'rtl/{top}.ng45.log').read(); d=re.findall(r'Delay = *([0-9.]+) ps',log)
    st=json.load(open(f'rtl/{top}.ng45.json')); mod=st['modules']['\\'+top]
    area=mod.get('area'); cells=mod['num_cells']
    print(f'| {top} | {cells} | {area:.2f} | {area/NAND2:.1f} | {d[-1] if d else "n/a"} |')
