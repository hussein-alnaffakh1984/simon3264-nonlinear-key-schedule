# A nonlinear key schedule for Simon 32/64: reproducible analysis

Code and results accompanying the manuscript *A Nonlinear Key Schedule for Simon 32/64: Related-Key and Rotational-XOR Trail Bounds
and Weak-Key Cost* by Zainab H. Jassim, Hussein Ali Hussein Al Naffakh and Umar Farooq Khattak.

**Status: under review, not peer reviewed.** The schedule called `v3` is an experimental research variant of the Simon 32/64 key
schedule. It is not a standard and must not be used to protect real data.

Requirements: Python 3.10+, `pip install numpy python-sat` (PySAT 1.8+, solver CaDiCaL 1.5.3). No GPU, no internet.

| File | Purpose |
|---|---|
| `simon_ks.py` | Reference cipher and key schedules `std`, `v2`, `v3`; self-test on import (official vector c69b e9bb; v3 vector c619 41b4) |
| `trail_search.py` | SAT search for minimum-weight trails: single-key (`sk`), related-key (`rk`), rotational-XOR (`rx`, `--gamma`), objective `total` or `data` (weak-key) |
| `verify_trails.py` | Seeded experimental check of every found trail with the real cipher |
| `results/` | Logs and trails (`.jsonl`) from the runs reported below |

Determinism: the SAT search has no randomness (same command, same weights). Experiments use numpy PCG64 with seed 20261126
(sub-streams derived from `[seed, rounds, weight]`); pass another seed as the third argument to `verify_trails.py`.

## Commands and results (2-vCPU VM; times are indicative)

Model validation against published values (Simon32, single-key optimal weights; RX with gamma=1):
```
python3 trail_search.py std sk 1 9                      # 0 2 4 6 8 12 14 18 20
python3 trail_search.py std rx 5 9 --gamma 1 --out results/rx_g1_std.jsonl   # 0 0 4 6 10
```
Proposed schedule, all keys (objective total = data weight + key-schedule weight):
```
python3 trail_search.py v3 rx 5 10 --gamma 1 --out results/rx_g1_v3.jsonl    # 0 0 4 8 14 22
```
Proposed schedule, weak-key setting (objective data; key-schedule transitions free):
```
python3 trail_search.py v3 rx 7 10 --gamma 1 --objective data   # data 4 6 8 11  (key weight of found trail 4 2 24 29)
python3 trail_search.py v3 rk 6 9 --objective data              # data 2 4 6 8   (key weight of found trail 4 2 23 24)
```
Experimental verification (2^22 samples per trail):
```
python3 verify_trails.py results/rx_g1_std.jsonl 22     # see results/verify_rx_g1_std.txt
python3 verify_trails.py results/rx_g1_v3.jsonl 22      # see results/verify_rx_g1_v3.txt
```

## Not done yet
RX for gamma = 2..15; std RX at 10+ rounds (did not finish in 25 min; published value to be compared); minimum key weight for each
data weight in the weak-key setting; weak-key trails (key weight 23–29) are not verified by experiment; rounds beyond 10.

## Added 26 Nov, evening: weak-key trade-off and reduced-gate variants
Kinds `v3m<hexmask>` = v3 with the key-schedule AND output masked (v3m0101: 2 gates, v3m1111: 4, v3m5555: 8, v3 = v3mffff: 16).
Objective `key --dmax D` = minimum key-schedule weight among trails with data weight <= D.
```
python3 trail_search.py v3m0101 rk 6 9 --objective data     # 2 4 8 11   (equals std)
python3 trail_search.py v3m0101 rx 7 9 --objective data     # 4 6 10     (equals std)
python3 trail_search.py v3m1111 rk 6 9 --objective data     # 2 4 8 8    (key weight of found trail 0 2 8 8)
python3 trail_search.py v3m5555 rk 6 9 --objective data     # 2 4 7 8
python3 trail_search.py v3 rk 8 8 --objective key --dmax 6  # 21 ; --dmax 7 -> 15 ; --dmax 8 -> 10
python3 trail_search.py v3 rx 9 9 --objective key --dmax 8  # 17
```
Unfinished within 200 s per instance: v3 rk 9 rounds with --dmax 8..11; v3 rx 10 rounds with --dmax 11..13; v3 rx 9 rounds --dmax 9.

## Added 26 Nov, night: weak-key trails verified with real keys; all rotation amounts
```
python3 verify_weak.py results/curve_v3_rk.jsonl 27 14      # results/verify_weak_rk.txt
python3 verify_weak.py results/curve_v3_rx.jsonl 27 14      # results/verify_weak_rx.txt
for g in $(seq 1 15); do for k in std v3; do python3 trail_search.py $k rx 8 8 --gamma $g --out results/rx_allgamma.jsonl; done; done
python3 trail_search.py v3 rk 9 9 --objective key --dmax 8  # 24 (251 s)
```
8-round RX, minimum total weight for gamma = 1..15:  std 6 4 6 6 7 7 6 8 6 7 7 6 6 4 6 ;  v3 8 8 8 11 11 10 8 10 8 10 11 11 8 8 8.
Unfinished within 570 s: v3 rk 9 rounds --objective key --dmax 11.

## Added 26 Nov, late night
- 9-round RX for every rotation amount (`results/rx_allgamma_r9.jsonl`, checked in `results/verify_rx_allgamma_r9.txt`):
  std 10 10 10 10 (g=5 unfinished in 420 s) 11 11 12 11 11 12 10 10 10 10 ; v3 14 14 16 18 18 18 14 19 14 18 18 18 16 14 14.
- v3 related-key, 9 rounds, all keys: 19 exactly (`python3 trail_search.py v3 rk 9 9 --start 15`, 59 s).
- `cost_v3/`: C implementation, benchmark, code sizes (x86-64, AVR, Cortex-M0), Verilog and Yosys synthesis of the v3 round update.
- `results/neural_v3.log`: related-key MLP distinguisher on v3 (same script and budget as for the other variants).
- Unfinished: v3 related-key 10 rounds (900 s), curve point 9 rounds data <= 11 (700 s), std RX 10 rounds (25 min).

## Added 26 Nov, night (search improvements and 10/11-round bounds)
`trail_search.py` now adds, by default, Matsui-style sub-trail bounds from the already proven optima (`KNOWN`) and a rotational
symmetry-breaking constraint for XOR-difference searches (`--no-matsui` disables the former). Same optima, about 1.5-3x faster.
New one-shot query `--bound W`: either returns a trail of weight <= W or proves that none exists (minimum >= W+1).
```
python3 trail_search.py v3 rk 10 10 --bound 21             # NO TRAIL: minimum >= 22   (118 s)
python3 trail_search.py v3 rk 11 11 --bound 24             # NO TRAIL: minimum >= 25   (137 s)
python3 trail_search.py v3 rx 11 11 --gamma 1 --bound 24   # NO TRAIL: minimum >= 25   (115 s)
python3 trail_search.py v3 rx 11 11 --gamma 1 --bound 29   # TRAIL of weight 29 (21 + 8) (168 s)
```
No answer within 560 s: `std rk 10 10 --bound 15`, `std rx 10 10 --gamma 1 --bound 14`.

## Figures
`python3 make_figures.py` writes `figures/fig1_schedule`, `fig2_trail_weights`, `fig3_weak_key` as PDF (vector), PNG (600 dpi) and TIFF (1200 dpi, LZW).
Every plotted value is one of the results listed above.

## Added 26 Nov, after external review
```
python3 verify_and_layer.py                                   # all 65,535 input differences: 0 mismatches with the model, zero output difference always possible (21 s)
python3 trail_search.py std rx 9 9 --gamma 5 --bound 9        # NO TRAIL: minimum >= 10 (11 s)  -> minimum over all 15 rotations at 9 rounds is 10
python3 trail_search.py std rk 10 10 --bound 21               # TRAIL of weight 21 (222 s)       -> Simon <= 21 < 22 <= v3
python3 trail_search.py std rk 11 11 --bound 24               # TRAIL of weight 24 (44 s)        -> Simon <= 24 < 25 <= v3
python3 verify_weak.py <file with the 9-round trail, w_key 24> 30 14   # 534 keys of 2^30: density 2^-20.94, NOT 2^-24 (results/verify_weak_rk9.txt)
```
The last line shows that key-schedule conditions of one trail are not independent: the model key weight (24) overestimates the true one (20.94).
Neural distinguisher with five seeds (std: 0.655-0.699 at 10 rounds, 0.500-0.504 at 11; v3: 0.874-0.877 at 8, 0.502-0.506 at 9).

## Added 26–27 Nov: Simeck, real cell library, microcontroller cycles, class counting
```
python3 simeck.py selftest                       # Simeck32/64 test vector 770d 2c76; AND-layer model exact for all 65,535 differences
python3 simeck.py rk 6 11                        # 2 4 8 10 14 18          (all keys)
python3 simeck.py rk 6 10 --objective data       # 2 2 4 6 8               (weak keys, data weight)
python3 simeck.py rx 5 11 --gamma 1              # 0 0 2 6 10 14 21
python3 simeck.py rx 7 11 --gamma 1 --objective data   # 2 4 4 6 8
python3 count_class.py results/curve_v3_rk.jsonl # key-class size by approximate model counting (pip install pyapproxmc)
```
`count_class.py` gave 20.99, 15.03, 10.00 (8 rounds) and 21.05 (9 rounds; trail model says 24), in line with direct sampling
(20.93, 14.99, 10.00, 20.94). CAUTION: on one trivial 5-round RX instance it returned 2^48 where every key qualifies (2^64, confirmed
by sampling and by a SAT check); the cause was not found, so counts are reported only where sampling confirms them.

`cost_v3/`: `rtl/synth_ng45.py` synthesises to the NanGate 45 nm Open Cell Library. The library file is not redistributed here; it
was taken from github.com/The-OpenROAD-Project/OpenROAD-flow-scripts (flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib)
and must be placed at `rtl/ng45.lib`. Results (`synth_ng45_output.txt`): round update 98.0 -> 146.0 GE, round-serial 667.0 -> 713.3 GE.
`avr_bench.c` + simavr (ATmega328P, -Os): empty call 74, std 1900, v3 2280 timer counts, identical for three keys.
