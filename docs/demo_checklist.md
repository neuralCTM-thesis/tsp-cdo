# Pre-recording checklist


## The day before
- [ ] Real data entered in `data/` and the validator passes: `python main.py --validate`.
- [ ] The console shows **no** "PLACEHOLDER DATA" banner, and the figures have no red watermark.
- [ ] `python -m pytest` → all tests pass.
- [ ] `python main.py --experiments` has been run with the real data (about 3 min); `docs/` shows its tables.
- [ ] `python main.py --find-demo-seed`, then put the suggested seed into `DEFAULT_SEED` in `src/config.py`. The demo seed reaches the optimum, and its first 5 moves show an improvement, an accepted worse move and a rejection. Current seed: **1**.
- [ ] `python main.py` once more, then `python main.py --check-consistency` → everything PASS.
- [ ] Slides rebuilt from `docs/slides_outline.md` (numbers copied from `docs/results_tables.md`, not retyped).
- [ ] Names, course and section on the title slide (in the deck already; add the instructor and date if required).

## Screen and recording setup
- [ ] Resolution 1920×1080; record the full screen or one window.
- [ ] Terminal / VS Code font **≥ 18 pt** (VS Code: `Ctrl` + `=` twice). Use a light theme for contrast.
- [ ] Terminal window at least 110 characters wide, so the tables do not wrap.
- [ ] Jupyter (if you use `demo.ipynb`): zoom 125–150%, **Kernel → Restart & Clear Output** before recording.
- [ ] Browser tab with `outputs/route_map.html` ready (internet on, so the map tiles load).
- [ ] Image viewer with `fig4_convergence.png`, `fig5_acceptance.png` and `fig6_sa_animation.gif` ready.
- [ ] Close chat apps, e-mail and notifications (Windows: Focus Assist on). Hide the desktop icons.
- [ ] Microphone test: 10 s recording, play it back, no echo or fan noise.

## During the recording
- [ ] Show the input CSVs **before** running the code (the rubric requires input, run and output).
- [ ] Type the command live: `python main.py --trace`. Do not paste screenshots.
- [ ] Scroll slowly; pause 2–3 s on the trace, the verification table and the optimality check.
- [ ] Say the total with units: "**14.1 kilometres**".
- [ ] Say "optimal for this instance, **proven by brute force**", never "SA guarantees the optimum".

## Timing (target 12:45, allowed 10:00–15:00)
| Section | Planned | Actual |
|---|---|---|
| A. Intro, problem, objective | 2:30 | |
| B. Simulated Annealing | 2:45 | |
| C. Graph, data, methodology | 2:30 | |
| D. Live run and results | 3:45 | |
| E. Conclusion, references | 1:15 | |
| **Total** | **12:45** | |

## Submission bundle
- [ ] Video file (MP4), 10–15 min.
- [ ] Code: the whole `tsp_sa_cdo/` folder (or a zip) including `main.py`, `src/`, `demo.ipynb`, `requirements.txt`, `README.md`.
- [ ] Dataset: `data/locations.csv`, `data/distance_matrix.csv`, `data/data_sources.csv`.
- [ ] References in the slides **and** in `REFERENCES.md`.

---
_Generated 2026-10-17 18:49 from data fingerprint `c652b67ace` by `src/docs_builder.py`. Do not edit by hand; edit `docs/templates/demo_checklist.md.tmpl` instead._
