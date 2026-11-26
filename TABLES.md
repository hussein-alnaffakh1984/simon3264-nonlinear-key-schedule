# Where each table and figure of the manuscript comes from

All commands are run from the repository root. Searches are deterministic; experiments use seed 20261126 unless a seed is given.

| Item | Result files | Command |
|---|---|---|
| Validation (Section 4.1): single-key optima | printed | `python3 trail_search.py std sk 1 9` |
| Validation: AND-layer model, all 65,535 differences | `results/verify_and_layer.txt` | `python3 verify_and_layer.py` |
| Table 1, rounds 6–9 | `results/rk_v3_total_long.jsonl`, logs in `results/` | `python3 trail_search.py std rk 6 9` ; `python3 trail_search.py v3 rk 6 9` ; `python3 trail_search.py v3 rk 6 9 --objective data` |
| Table 1, rounds 10–11 | `results/bounds.jsonl` | `python3 trail_search.py v3 rk 10 10 --bound 21` ; `... v3 rk 11 11 --bound 24` ; `... std rk 10 10 --bound 21` ; `... std rk 11 11 --bound 24` |
| Table 2, rotation 1 | `results/rx_g1_std.jsonl`, `results/rx_g1_v3.jsonl`, `results/rx_g1_v3_data.jsonl`, `results/bounds.jsonl` | `python3 trail_search.py <std|v3> rx 5 10 --gamma 1` ; `python3 trail_search.py v3 rx 7 10 --gamma 1 --objective data` ; `python3 trail_search.py v3 rx 11 11 --gamma 1 --bound 24` (and `--bound 29`) |
| Table 2, all rotations | `results/rx_allgamma.jsonl`, `results/rx_allgamma_r9.jsonl`, `results/bounds.jsonl` | `for g in $(seq 1 15); do python3 trail_search.py <std|v3> rx 8 9 --gamma $g; done` ; `python3 trail_search.py std rx 9 9 --gamma 5 --bound 9` |
| Table 3 | `results/curve_v3_rk.jsonl`, `results/curve_v3_rx.jsonl`, `results/verify_weak_rk.txt`, `results/verify_weak_rx.txt`, `results/verify_weak_rk9.txt` | `python3 trail_search.py v3 rk 8 8 --objective key --dmax <6|7|8>` ; `... v3 rk 9 9 --objective key --dmax 8` ; `... v3 rx 9 9 --objective key --dmax 8` ; `python3 verify_weak.py <file> 27 14` (30 for the 9-round class) |
| Table A1 (17 further key classes, Section 4.4) | `results/classes2.jsonl`, `results/verify_classes2.txt` | `for g in $(seq 1 8); do python3 trail_search.py v3 rx 8 9 --gamma $g --objective data --out results/classes2.jsonl; done` ; `python3 trail_search.py v3 rk 7 8 --objective data --out results/classes2.jsonl` ; `python3 verify_weak.py results/classes2.jsonl 29 13` |
| Table 4 | `results/*_m1111_*`, `results/*_m5555_*`, `results/rk_lite_*` | `python3 trail_search.py v3m<0101|1111|5555> rk 6 9 [--objective data]` |
| Table 5, bit-bias rows | `results/bit_bias.txt` | `python3 bit_bias.py 18` |
| Table 5 (last row) and Table 6 | `results/neural_seeds/*.json` | `python3 neural_distinguisher.py <std|v3> 6 <rmin> <rmax> <seed 1..5>` |
| Table 7 | `cost_v3/synth_ng45_output.txt`, `cost_v3/bench_output.txt`, `cost_v3/sizes_output.txt` | see `cost_v3/` (`rtl/synth_ng45.py`, `avr_bench.c` with simavr, `main.c`) |
| Table 8 | `results/simeck_*.jsonl` | `python3 simeck.py selftest` ; `python3 simeck.py <rk|rx> 6 11 [--objective data]` |
| Trail verification (Section 4.5) | `results/verify_rx_g1_*.txt`, `results/verify_rx_allgamma_r9.txt` | `python3 verify_trails.py <trail file> 22` |
| Key-bit dependence and Hamming distance (Sections 3.5 and 4.5) | `results/key_dependence.txt` | `python3 key_dependence.py 16` |
| Figures 1–3 | `figures/` | `python3 make_figures.py` |

In the code the proposed schedule is called `v3` and the standard one `std`.
