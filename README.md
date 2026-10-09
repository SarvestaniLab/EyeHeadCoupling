# Eye-Head Coupling Analysis

Tools for studying the relationship between eye and head movements in rats and tree shrews.

## Directory Structure
- `MATLAB/` – legacy MATLAB code.
- `Python/` – all Python analysis code, utilities and notebooks.
- `session_manifest.yml` – session configuration file in the root directory.

## Setup
1. Clone the repository
   ```
   git clone https://github.com/SarvestaniLab/EyeHeadCoupling.git
   cd EyeHeadCoupling
   ```
2. Create the conda environment
   ```
   conda env create -f Python/EyeHeadCoupling.yml
   ```
3. Activate the environment
   ```
   conda activate EyeHeadCoupling
   ```

## Session Manifest
Session metadata lives in `session_manifest.yml` and maps session identifiers to their settings:
```yaml
sessions:
  session_01:
    session_path: /path/to/session_01
    results_dir: /path/to/session_01/results
```

Use `utils.session_loader.load_session` to access entries.

### Two manifests: live and paper
- `session_manifest.yml` (repo root) is the **live** list. It grows as experiments
  continue, and the scripts in `Python/analysis/` read it by default.
- `Python/paper_figures/paper_manifest.yml` is the **frozen** list behind the paper's
  figures: which sessions each figure uses, the settings they were analysed with, and
  the folders to read from and write to. The scripts in `Python/paper_figures/` read
  only this file, so adding sessions or changing settings in the live manifest cannot
  change a paper figure. To use the data from another location, edit `data_root` (and
  the output folders) at the top of that file.

Both files share one format, so the pipeline can be run on the paper's sessions:
```
python Python/analysis/prosaccade_population.py --manifest Python/paper_figures/paper_manifest.yml --quiet-session-plots
```

## Paper figures
Which script makes which figure. Python scripts are in `Python/paper_figures/` and take
no arguments: `python Python/paper_figures/<script>`. Each writes a PNG and an SVG.

| Figure | Shows | Script | Reads |
|---|---|---|---|
| 1, S1 | Saccades without head movement: eye and attempted head movement, main sequences | `MATLAB/Figure2_EyeHead/EyeHeadCouplingAnalysis.m`, then `EyeHeadCouplingAnalysis_populationPlots.m` (to confirm; the folder name predates the final figure numbering) | session list in `file_database.mat`; raw sessions |
| 2, S2 | Gaze shifts in the binocular visual field | not in this repository (to confirm) | |
| 3, S3A | Saccades to a visual target: one example session, the population, and each animal separately | `Fig3_prosaccade.py` | paper manifest; raw sessions; the population cache (see below) |
| S3C–D | Torsion saccades by target position, two example sessions | `Fig3S_prosaccade_torsion.py` | paper manifest; raw sessions |
| 4 | Cued fixation and fixation on a target with gaze feedback | `Fig4_fixation.py` | paper manifest; raw sessions |
| S4 | Gaze heatmaps for three target positions | `Fig4S_fixation_heatmap.py` | paper manifest; raw sessions |
| 5 | Share of V1 devoted to the central visual field: tree shrew, squirrel monkey, mouse | `Fig5_cortex.py` | `Python/paper_figures/Fig5_inputs/` (in this repository) |
| 6 | Extraocular muscle histology | none (no analysis code) | |

Schematic panels (task diagrams, 3-D renders) are made in other software and are not
drawn by these scripts; the figure scripts leave space for them.

- **Raw sessions** are not in this repository. The paper manifest's `data_root` says
  where they are; change that one line to use a copy elsewhere. Figure 5 needs none.
- **Figure 3's population cache** is built once, from the paper's sessions, with the
  `prosaccade_population.py --manifest ...` command above. `Fig3_prosaccade.py` stops with
  that command if the cache is missing or holds any other set of sessions.
- **Checks:** `pytest Python/tests` (tests that need the raw sessions skip without them).

## Usage
- Run analysis scripts from `Python/analysis/`. They read the live `session_manifest.yml`.
- Paper figure scripts are in `Python/paper_figures/` (table above).
- Launch Jupyter notebooks from `Python/notebooks/`.

## Plotting style
Matplotlib figures use a repository-wide style defined in `Python/style.mplstyle`.
The helper functions in `Python/eyehead/plotting.py` load this file with
``plt.style.use`` so that all plots share consistent fonts and colours.
