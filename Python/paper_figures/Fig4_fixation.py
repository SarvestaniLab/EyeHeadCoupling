"""Standalone script: one composite multi-panel figure for the two fixation
tasks (Figure 4 of the paper), cued fixation on top and gaze-contingent
fixation-on-target below.

This is a Python port of the MATLAB scripts that produced the published
panels (kept in ``X:\\Papers\\Active_vision_ts\\Figure4_Fixation``):

- ``fixation_sampletraces.m``            -> Panels B and C
- ``fixation_wfeedback_sampletraces.m``  -> Panels E and F
- ``fixation_wfeedback_population.m``    -> Panel G

The other three scripts in that folder (``fixation_session.m``,
``fixation_population.m``, ``fixation_wfeedback_session.m``) draw
exploratory per-session plots that are not part of Figure 4, so they are
not ported.

Layout
------
- Panel A: not drawn. Empty space is left for the hand-drawn cued-fixation
  schematic (added separately, e.g. in Illustrator).
- Panel B: two cued-fixation example sessions (400 ms criterion on top,
  700 ms below). Left: eye position on 4 sample trials, last 2.5 s before
  trial end. Middle: the same for 100 trials over the full trial. Right:
  histogram of every trial's duration.
- Panel C: for the same two sessions, the CDF of fixation durations found
  within trials vs. within the inter-trial interval (ITI).
- Panel D: not drawn. Empty space is left for the fixation-on-target
  schematic.
- Panel E: one fixation-on-target example session. Distance between the
  gaze-contingent marker and the target for 4 sample trials (left) and for
  every trial (right), successes on top and failures below.
- Panel F: that session's trial-duration histograms, successes and failures.
- Panel G: every fixation-on-target session of both animals: success rate
  and median duration of successful trials, marked by the session's required
  fixation time.

How faithful the port is
------------------------
The analysis is a line-for-line port and was checked against the data saved
inside the MATLAB ``.fig`` files: every trial duration, every detected
fixation duration (Panel C), the example session's outcome counts and every
population point (Panel G) agree exactly.

The MATLAB picked its sample trials at random (``randperm``) and the
published panels are whichever draw was saved. Those exact trials were
recovered from the ``.fig`` files and are listed below, so this script draws
the same traces on every run.

What "eye position" means in Panels B and C
-------------------------------------------
Both panels use one combined measure of eye position rather than its
horizontal and vertical components separately: ``sqrt(x**2 + y**2)`` of the
pupil centre in the camera image, converted to degrees (see
:data:`EYE_SIGNAL`). Panel B plots it with each trial's mean subtracted;
Panel C detects fixations on it.

- It responds to both horizontal and vertical eye movement. With the pupil
  where it sits in these recordings, it is close to 0.8 x horizontal +
  0.6 x vertical displacement, so the traces resemble horizontal position
  without being identical to it.
- It does not respond to movement at right angles to that direction, so a
  "fixation" is stable along one combined axis, not strictly in two
  dimensions. A stricter rule, requiring the horizontal and the vertical
  range each to stay within the limit, shortens fixations slightly and
  leaves Panel C's conclusion unchanged in both sessions; the published
  version is kept here.
- Set ``EYE_SIGNAL = "horizontal"`` to redo both panels on horizontal
  position alone. The numbers then no longer match the published figure.

Degrees come from a fixed 3.6 camera pixels per degree
(:data:`PIXELS_PER_DEG`), as in the MATLAB, not the 3.76 the manifest's
``calibration_factor`` lists for the same animals.

Which sessions
--------------
Fixed by the PAPER manifest (``paper_manifest.yml`` in this folder, block
``figures: Fig4``), not by the live ``session_manifest.yml``: the two cued
sessions of Panels B/C, the example session of Panels E/F, and -- for Panel
G -- every session of the ``population`` experiment type listed there, each
with its required fixation time (``fixation_ms``). Which TRIALS are drawn as
samples is a drawing choice and stays in this file (:data:`SAMPLE_TRIALS`,
:data:`FEEDBACK_SAMPLES`), keyed by session ID.

What is reused from the rest of the repo
----------------------------------------
- The cued-fixation sessions are read with the standard
  :func:`utils.session_loader.load_session` /
  :func:`eyehead.load_session_data` pair.
- The fixation-on-target sessions are read with
  :func:`prosaccade_feedback_session.load_feedback_data`, the loader
  ``Fig4S_fixation_heatmap.py`` already uses.
- Type sizes, tick style, panel letters and file saving all come from
  ``Fig3_prosaccade.py``, so Figures 3 and 4 cannot drift apart
  typographically.

Inputs and outputs
------------------
Read from each session folder (Bonsai CSVs):

- cued fixation: ``ellipse_center_XY_L`` (pupil centre), ``vstim_cue`` (cue
  onsets), ``endoftrial`` (trial ends).
- fixation on target: ``vstim_go`` (gaze-marker position and size),
  ``vstim_cue`` (target position and size), ``endoftrial`` (trial ends and
  outcomes).

Written: ``Fig4_fixation.png`` and ``Fig4_fixation.svg`` in this figure's
``output_dir`` from the paper manifest, plus a console summary of the numbers quoted in the paper's text and legend (trial counts,
medians, success rates).

Usage
-----
No CLI arguments. Sessions and the output folder are set in
``paper_manifest.yml`` (``figures: Fig4``); sample trials and analysis
parameters are set near the top of this file. Then run:

    python Python/paper_figures/Fig4_fixation.py

Checks live in ``Python/tests/test_fig4_fixation.py``.
"""
from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import numpy as np
import matplotlib.pyplot as plt

from paper_figures.Fig3_prosaccade import (
    FONT_SIZE_LABEL,
    FONT_SIZE_TICK,
    _annotate_n,
    _apply_paper_style,
    _limit_ticks,
    _panel_letter,
    _save,
    _strip_box,
)
from analysis.prosaccade_feedback_session import load_feedback_data
from eyehead import load_session_data
from paper_figures import paper_manifest
from utils.session_loader import load_session

# ---------------------------------------------------------------------------
# Run configuration
# ---------------------------------------------------------------------------
### The sessions and the output folder come from the paper manifest
### (paper_manifest.yml in this folder, block "figures: Fig4"), so they are
### frozen for the paper. Change them there, not here.
_FIGURE = paper_manifest.figure("Fig4")
OUTPUT_STEM = paper_manifest.output_dir("Fig4") / "Fig4_fixation"

### MATLAB's default line colors (``lines``), which the sample-trace panels
### were drawn in.
MATLAB_BLUE, MATLAB_ORANGE, MATLAB_YELLOW, MATLAB_PURPLE = (
    "#0072BD", "#D95319", "#EDB120", "#7E2F8E")
MATLAB_LIGHT_BLUE, MATLAB_DARK_RED = "#4DBEEE", "#A2142F"
DEFAULT_SAMPLE_COLORS = [MATLAB_BLUE, MATLAB_ORANGE, MATLAB_YELLOW, MATLAB_PURPLE]

### Panels B/C: which trials are drawn for each cued-fixation session, keyed
### by session ID.
###
### ``sample_trials`` (Panel B, left) and ``overview_trials`` (Panel B,
### middle) are 0-based positions in the session's trial list -- the exact
### trials of the published panels, recovered from the MATLAB .fig files.
### ``overview_trials`` is a random 100 of the session's trials, NOT all of
### them; set it to None to draw every trial instead.
SAMPLE_TRIALS = {
    "Tsh002_2025-09-05T10_59_22": dict(
        sample_trials=[44, 114, 103, 14],
        sample_colors=[MATLAB_BLUE, MATLAB_LIGHT_BLUE, MATLAB_DARK_RED, MATLAB_ORANGE],
        overview_trials=[
            115, 23, 84, 33, 66, 38, 123, 27, 65, 94, 58, 63, 60, 30, 0, 57, 77,
            98, 114, 2, 7, 29, 13, 69, 124, 22, 11, 49, 73, 45, 46, 88, 78, 109,
            103, 76, 50, 100, 91, 26, 12, 48, 44, 17, 74, 51, 85, 14, 19, 90, 37,
            41, 55, 92, 71, 4, 96, 80, 99, 42, 72, 59, 47, 75, 21, 70, 89, 35, 52,
            122, 82, 25, 110, 61, 53, 67, 125, 97, 6, 31, 102, 87, 9, 81, 105,
            113, 79, 119, 24, 64, 36, 1, 86, 15, 43, 3, 62, 8, 39, 121,
        ],
    ),
    "Tsh002_2025-09-15T11_41_54": dict(
        sample_trials=[15, 227, 43, 36],
        sample_colors=[MATLAB_BLUE, MATLAB_ORANGE, MATLAB_YELLOW, MATLAB_PURPLE],
        overview_trials=[
            172, 10, 35, 199, 24, 104, 38, 119, 138, 208, 130, 246, 192, 236,
            142, 194, 34, 29, 128, 232, 39, 98, 127, 105, 110, 108, 163, 20, 56,
            243, 25, 238, 79, 237, 212, 259, 221, 61, 103, 65, 91, 234, 150, 188,
            107, 224, 240, 5, 209, 37, 73, 134, 176, 148, 210, 153, 2, 36, 255,
            157, 60, 117, 201, 3, 166, 189, 11, 182, 97, 54, 180, 197, 135, 129,
            245, 178, 228, 131, 191, 92, 144, 251, 88, 13, 170, 190, 247, 112,
            250, 155, 55, 241, 137, 231, 160, 1, 50, 126, 12, 42,
        ],
    ),
}


def _cued_sessions():
    """The paper manifest's cued sessions, each with its required fixation
    time and the trials to draw. A session with no entry in
    :data:`SAMPLE_TRIALS` (one newly swapped into the manifest) gets its
    first four trials as samples and every trial in the overview."""
    sessions = []
    for session_id in _FIGURE["cued_sessions"]:
        drawn = SAMPLE_TRIALS.get(session_id, dict(
            sample_trials=[0, 1, 2, 3],
            sample_colors=DEFAULT_SAMPLE_COLORS,
            overview_trials=None,
        ))
        criterion_ms = paper_manifest.session(session_id).params["fixation_ms"]
        sessions.append(dict(criterion_ms=criterion_ms, session_id=session_id, **drawn))
    return sessions


CUED_SESSIONS = _cued_sessions()

### Panel G: every fixation-on-target session in the paper manifest, as
### (session ID, required fixation time in ms). 500 ms was the standard
### criterion; each animal also ran one shorter (400 ms) and one longer
### (700 ms) session.
FEEDBACK_SESSIONS = [
    (session_id, paper_manifest.session(session_id).params["fixation_ms"])
    for session_id in paper_manifest.sessions_of_type(_FIGURE["population"])
]

### Panels E/F: the example session, and which of its trials Panel E (left)
### draws. Positions are 0-based within the session's successful / failed
### trials, so MATLAB's trial "#5" is 4 here. As above, a session with no
### entry falls back to its first four trials of each kind.
FEEDBACK_EXAMPLE_SESSION = _FIGURE["example_session"]
FEEDBACK_SAMPLES = {
    "Tsh001_2025-11-24T14_28_34": dict(successes=[4, 37, 69, 10], failures=[20, 13, 9, 25]),
}
_example_samples = FEEDBACK_SAMPLES.get(
    FEEDBACK_EXAMPLE_SESSION, dict(successes=[0, 1, 2, 3], failures=[0, 1, 2, 3]))
FEEDBACK_SAMPLE_SUCCESSES = _example_samples["successes"]
FEEDBACK_SAMPLE_FAILURES = _example_samples["failures"]
FEEDBACK_SAMPLE_COLORS = [MATLAB_BLUE, MATLAB_ORANGE, MATLAB_YELLOW, MATLAB_PURPLE]

# ---------------------------------------------------------------------------
# Analysis parameters — the values the MATLAB scripts used.
# ---------------------------------------------------------------------------
### Which measure of eye position Panels B and C are computed from:
###   "radial"     sqrt(x**2 + y**2) of the pupil centre, which combines
###                horizontal and vertical movement. What the MATLAB used;
###                reproduces the paper.
###   "horizontal" horizontal pupil position alone.
EYE_SIGNAL = "radial"

PIXELS_PER_DEG = 3.6  # camera pixels per degree of eye rotation

### The gaze-contingent marker's position is logged in Bonsai stimulus
### units. Dividing by the Bonsai linear-mapping gain (0.06 units per camera
### pixel) takes it back to camera pixels, and PIXELS_PER_DEG to degrees of
### eye rotation.
BONSAI_UNITS_PER_PIXEL = 0.06
FEEDBACK_DEG_PER_UNIT = (1.0 / BONSAI_UNITS_PER_PIXEL) / PIXELS_PER_DEG

TRIAL_END_TRIM_S = 0.05   # cued task: drop the last 50 ms before trial end
POST_TRIAL_S = 2.0        # feedback task: keep 2 s of gaze after trial end

### Fixation detection (Panel C).
FIX_MAX_RANGE_DEG = 0.6     # a fixation's signal stays within this range
FIX_MIN_DURATION_S = 0.2    # shorter stable stretches are discarded
FIX_MIN_SACCADE_DEG = 5.0   # stretches split by less than this may be merged
FIX_MIN_RANGE_DEG = 0.05    # flatter than this is a dead signal, not a fixation
ITI_TAIL_S = 1.5            # only the last 1.5 s of each ITI is searched

### Trial-duration histograms (Panels B and F): 19 bins spanning 0-12 s.
DURATION_BIN_EDGES = np.linspace(0, 12, 20)

# ---------------------------------------------------------------------------
# Styling constants — colors of the published figure.
# ---------------------------------------------------------------------------
TRIAL_COLOR = "#00A14B"     # within-trial data, and successful trials
FAIL_COLOR = "#ED1C24"      # failed trials
ITI_COLOR = "0.6"           # inter-trial-interval fixations
TRIAL_END_COLOR = "#ED1C24"  # dashed line marking trial end
ZERO_LINE_COLOR = "0.8"     # distance-to-target = 0

### Panel G: one marker and color per required fixation time.
CRITERION_STYLE = {
    400: dict(marker="s", color="#2673E6"),
    500: dict(marker="o", color="#00A14B"),
    700: dict(marker="^", color="#D63821"),
}
STANDARD_CRITERION_MS = 500   # the criterion whose mean +/- SD is drawn
JITTER_WIDTH = 0.35           # horizontal spread of Panel G's session markers


# ---------------------------------------------------------------------------
# Analysis: fixation detection
# ---------------------------------------------------------------------------

def _eye_signal(x, y):
    """The 1-D eye signal selected by :data:`EYE_SIGNAL` (degrees)."""
    if EYE_SIGNAL == "radial":
        return np.hypot(x, y)
    if EYE_SIGNAL == "horizontal":
        return np.asarray(x, dtype=float)
    raise ValueError(f"EYE_SIGNAL must be 'radial' or 'horizontal', not {EYE_SIGNAL!r}")


def find_fixation_segments(t, signal, max_range=FIX_MAX_RANGE_DEG,
                           min_duration=FIX_MIN_DURATION_S,
                           min_saccade=FIX_MIN_SACCADE_DEG,
                           min_range=FIX_MIN_RANGE_DEG):
    """Split ``signal`` into fixations: stretches that stay within ``max_range``.

    Three steps, as in the MATLAB ``find_fixation_segments``:

    1. Walk through the samples, growing a run for as long as its range
       (max - min) stays within ``max_range``. The sample that breaks the
       range starts the next run, so the runs tile the whole signal.
    2. Merge a run into the segment before it when the two are not separated
       by a movement of at least ``min_saccade`` AND the merged segment still
       stays within ``max_range``.
    3. Keep segments lasting at least ``min_duration`` whose range is at
       least ``min_range`` (a perfectly flat signal is a tracking dropout).

    Returns
    -------
    (starts, ends) : two lists of int
        Inclusive sample indices of each fixation's first and last sample.
    """
    t = np.asarray(t, dtype=float)
    signal = np.asarray(signal, dtype=float)
    n = signal.size

    run_starts, run_ends = [], []
    i = 0
    while i < n:
        lo = hi = signal[i]
        j = i + 1
        while j < n:
            lo = min(lo, signal[j])
            hi = max(hi, signal[j])
            if hi - lo > max_range:
                break
            j += 1
        run_starts.append(i)
        run_ends.append(j - 1)
        i = j
    if not run_starts:
        return [], []

    starts, ends = [run_starts[0]], [run_ends[0]]
    for run_start, run_end in zip(run_starts[1:], run_ends[1:]):
        gap = signal[ends[-1]:run_start + 1]
        merged = signal[starts[-1]:run_end + 1]
        if np.ptp(gap) < min_saccade and np.ptp(merged) <= max_range:
            ends[-1] = run_end
        else:
            starts.append(run_start)
            ends.append(run_end)

    kept = [(a, b) for a, b in zip(starts, ends)
            if t[b] - t[a] >= min_duration and np.ptp(signal[a:b + 1]) >= min_range]
    return [a for a, _ in kept], [b for _, b in kept]


def fixation_durations(t, signal):
    """Duration (s) of every fixation found in ``signal``."""
    t = np.asarray(t, dtype=float)
    starts, ends = find_fixation_segments(t, signal)
    return [float(t[b] - t[a]) for a, b in zip(starts, ends)]


# ---------------------------------------------------------------------------
# Analysis: cued fixation task (Panels B and C)
# ---------------------------------------------------------------------------

def build_cued_trials(eye_t, eye_x, eye_y, cue_t, eot_t):
    """One dict per trial of the cued fixation task.

    Each end-of-trial event is paired with the nearest cue onset before it;
    the trial is the eye samples from that cue up to ``TRIAL_END_TRIM_S``
    before the trial end. Trials with fewer than 2 eye samples are skipped.

    Each trial holds ``t`` (s, relative to trial end, so always negative),
    ``x`` / ``y`` (deg) and ``duration`` (s, cue onset to trial end).
    """
    trials = []
    for t_end in eot_t:
        preceding = np.flatnonzero(cue_t < t_end)
        if preceding.size == 0:
            continue
        t_start = cue_t[preceding[-1]]
        mask = (eye_t >= t_start) & (eye_t <= t_end - TRIAL_END_TRIM_S)
        if mask.sum() < 2:
            continue
        trials.append(dict(t=eye_t[mask] - t_end, x=eye_x[mask], y=eye_y[mask],
                           duration=float(t_end - t_start)))
    return trials


def trial_fixation_durations(trials):
    """Durations of every fixation found within the trials, pooled."""
    durations = []
    for trial in trials:
        durations.extend(fixation_durations(trial["t"], _eye_signal(trial["x"], trial["y"])))
    return np.asarray(durations, dtype=float)


def iti_fixation_durations(eye_t, eye_x, eye_y, cue_t, eot_t):
    """Durations of every fixation found in the inter-trial intervals, pooled.

    An ITI runs from one trial's end to the next cue onset. Only its last
    ``ITI_TAIL_S`` seconds are searched, so the comparison with within-trial
    fixations is not dominated by the reward period right after a trial.
    Samples logged as exactly (0, 0) are tracking dropouts and are removed.
    """
    durations = []
    for t_iti_start in eot_t[:-1]:
        following = np.flatnonzero(cue_t > t_iti_start)
        if following.size == 0:
            continue
        t_iti_end = cue_t[following[0]]
        mask = (eye_t >= t_iti_start) & (eye_t <= t_iti_end - TRIAL_END_TRIM_S)
        mask &= ~((eye_x == 0) & (eye_y == 0))
        if mask.sum() < 2:
            continue
        t = eye_t[mask]
        signal = _eye_signal(eye_x[mask], eye_y[mask])
        tail = t >= t_iti_end - ITI_TAIL_S
        if tail.sum() < 2:
            continue
        durations.extend(fixation_durations(t[tail], signal[tail]))
    return np.asarray(durations, dtype=float)


def analyze_cued_session(session_id: str) -> dict:
    """Trials, trial durations and fixation durations for one cued session.

    Read through the standard pipeline loader. It keeps one cue per trial by
    collapsing cue rows less than 1.5 s apart, where the MATLAB treated every
    row of the cue file as a trial onset; the two agree for these sessions,
    whose cues are always further apart than that.
    """
    with paper_manifest.frozen():
        data = load_session_data(load_session(session_id))
    eye_t = data.eye_timestamp
    eye_x = data.eye_x / PIXELS_PER_DEG
    eye_y = data.eye_y / PIXELS_PER_DEG
    cue_t, eot_t = data.cue_time, data.end_of_trial_ts

    trials = build_cued_trials(eye_t, eye_x, eye_y, cue_t, eot_t)
    if not trials:
        raise ValueError(f"No valid trials found in session {session_id!r}.")
    return dict(
        session_id=session_id,
        trials=trials,
        durations=np.array([trial["duration"] for trial in trials]),
        trial_fixations=trial_fixation_durations(trials),
        iti_fixations=iti_fixation_durations(eye_t, eye_x, eye_y, cue_t, eot_t),
    )


# ---------------------------------------------------------------------------
# Analysis: fixation-on-target task with gaze feedback (Panels E, F and G)
# ---------------------------------------------------------------------------

def build_feedback_trials(eot_df, eye_df, target_df):
    """One dict per trial of the fixation-on-target task.

    Takes the three dataframes returned by
    :func:`prosaccade_feedback_session.load_feedback_data`. Each end-of-trial
    event is paired with the nearest target onset before it; the trial is
    the gaze-marker samples from that onset to ``POST_TRIAL_S`` after the
    trial end.

    Each trial holds ``t`` (s, relative to trial end), ``distance`` (deg,
    the gap between the edge of the gaze marker and the edge of the target,
    so negative while they overlap), ``duration`` (s) and ``success``.

    The end-of-trial file codes outcome as a number whose meaning changed
    across rig versions; in every version the highest code present is the
    rewarded one, so that is what counts as a success.
    """
    eye_t = eye_df["timestamp"].to_numpy(dtype=float)
    eye_x = eye_df["green_x"].to_numpy(dtype=float) * FEEDBACK_DEG_PER_UNIT
    eye_y = eye_df["green_y"].to_numpy(dtype=float) * FEEDBACK_DEG_PER_UNIT
    eye_radius = eye_df["diameter"].to_numpy(dtype=float) * FEEDBACK_DEG_PER_UNIT / 2.0

    target_t = target_df["timestamp"].to_numpy(dtype=float)
    target_x = target_df["target_x"].to_numpy(dtype=float) * FEEDBACK_DEG_PER_UNIT
    target_y = target_df["target_y"].to_numpy(dtype=float) * FEEDBACK_DEG_PER_UNIT
    target_radius = target_df["diameter"].to_numpy(dtype=float) * FEEDBACK_DEG_PER_UNIT / 2.0

    eot_t = eot_df["timestamp"].to_numpy(dtype=float)
    outcome = eot_df["trial_success"].to_numpy()

    trials = []
    for i, t_end in enumerate(eot_t):
        preceding = np.flatnonzero(target_t < t_end)
        if preceding.size == 0:
            continue
        onset = preceding[-1]
        t_start = target_t[onset]
        mask = (eye_t >= t_start) & (eye_t <= t_end + POST_TRIAL_S)
        if mask.sum() < 2:
            continue
        center_distance = np.hypot(eye_x[mask] - target_x[onset], eye_y[mask] - target_y[onset])
        trials.append(dict(
            t=eye_t[mask] - t_end,
            distance=center_distance - target_radius[onset] - eye_radius[mask],
            duration=float(t_end - t_start),
            outcome=outcome[i],
        ))

    if trials:
        success_code = max(trial["outcome"] for trial in trials)
        for trial in trials:
            trial["success"] = bool(trial["outcome"] == success_code)
    return trials


def analyze_feedback_session(folder: Path) -> dict:
    """Trials and summary numbers for one fixation-on-target session."""
    folder = Path(folder)
    animal_id = folder.name.split("_")[0]
    ### load_feedback_data narrates every file it reads; with 14 sessions
    ### that buries this script's own summary, so it is silenced here.
    with contextlib.redirect_stdout(io.StringIO()):
        eot_df, eye_df, target_df = load_feedback_data(folder, animal_id)

    trials = build_feedback_trials(eot_df, eye_df, target_df)
    if not trials:
        raise ValueError(f"No valid trials found in {folder}.")
    successes = [trial for trial in trials if trial["success"]]
    failures = [trial for trial in trials if not trial["success"]]
    return dict(
        session_id=folder.name,
        animal_id=animal_id,
        trials=trials,
        successes=successes,
        failures=failures,
        success_rate=100.0 * len(successes) / len(trials),
        median_success_duration=float(np.median([trial["duration"] for trial in successes])),
    )


def resample_distance(trials, t_common):
    """Each trial's distance-to-target interpolated onto ``t_common``.

    Returns an (n_trials, len(t_common)) array, NaN wherever ``t_common``
    falls outside a trial's own time span. Panel E's all-trial traces are
    drawn from this common grid, as in the MATLAB.
    """
    resampled = np.full((len(trials), t_common.size), np.nan)
    for i, trial in enumerate(trials):
        inside = (t_common >= trial["t"].min()) & (t_common <= trial["t"].max())
        resampled[i, inside] = np.interp(t_common[inside], trial["t"], trial["distance"])
    return resampled


def run_analysis() -> dict:
    """Everything the figure draws: the cued example sessions, the feedback
    example session, and the feedback population."""
    cued = []
    for spec in CUED_SESSIONS:
        print(f"Analyzing cued-fixation session {spec['session_id']} ...")
        cued.append({**spec, **analyze_cued_session(spec["session_id"])})

    population = []
    for session_id, criterion_ms in FEEDBACK_SESSIONS:
        print(f"Analyzing fixation-on-target session {session_id} ...")
        folder = paper_manifest.session(session_id).folder_path
        population.append({"criterion_ms": criterion_ms, **analyze_feedback_session(folder)})

    by_id = {session["session_id"]: session for session in population}
    if FEEDBACK_EXAMPLE_SESSION not in by_id:
        raise KeyError(
            f"The paper manifest's Fig4 example_session "
            f"{FEEDBACK_EXAMPLE_SESSION!r} is not one of its "
            f"{_FIGURE['population']!r} sessions."
        )
    return dict(cued=cued, example=by_id[FEEDBACK_EXAMPLE_SESSION], population=population)


def print_summary(results: dict) -> None:
    """The numbers quoted in the paper's text and legend."""
    print("\n" + "=" * 70)
    print("Cued fixation (Panels B, C)")
    for session in results["cued"]:
        shown = session["overview_trials"]
        n_shown = len(session["trials"]) if shown is None else len(shown)
        print(f"  {session['criterion_ms']} ms criterion, {session['session_id']}:")
        print(f"    trials: n = {len(session['trials'])} ({n_shown} drawn in the "
              f"all-trials panel), median duration = {np.median(session['durations']):.2f} s")
        print(f"    fixations within trials: n = {session['trial_fixations'].size}, "
              f"median = {np.median(session['trial_fixations']):.2f} s")
        print(f"    fixations within ITIs:   n = {session['iti_fixations'].size}, "
              f"median = {np.median(session['iti_fixations']):.2f} s")

    example = results["example"]
    n_all, n_ok = len(example["trials"]), len(example["successes"])
    print("\nFixation on target, example session (Panels E, F)")
    print(f"  {example['session_id']}: {n_ok} of {n_all} trials successful "
          f"({example['success_rate']:.0f}%)")
    print(f"    median duration: successes = {example['median_success_duration']:.2f} s, "
          f"failures = {np.median([t['duration'] for t in example['failures']]):.2f} s")

    print(f"\nFixation on target, population (Panel G): n = {len(results['population'])} sessions")
    for session in results["population"]:
        print(f"  {session['session_id']}  {session['criterion_ms']} ms  "
              f"n = {len(session['trials']):3d}  success = {session['success_rate']:5.1f}%  "
              f"median successful duration = {session['median_success_duration']:.2f} s")
    for animal in sorted({session["animal_id"] for session in results["population"]}):
        standard = [s for s in results["population"]
                    if s["animal_id"] == animal and s["criterion_ms"] == STANDARD_CRITERION_MS]
        rates = [s["success_rate"] for s in standard]
        durations = [s["median_success_duration"] for s in standard]
        print(f"  {animal}, {STANDARD_CRITERION_MS} ms sessions (n = {len(standard)}): "
              f"success = {np.mean(rates):.1f} +/- {np.std(rates, ddof=1):.1f}%, "
              f"median duration = {np.mean(durations):.2f} +/- {np.std(durations, ddof=1):.2f} s "
              f"(mean +/- SD)")
    print("=" * 70 + "\n")


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def _mark_trial_end(ax):
    """Dashed line at t = 0, the end of the trial."""
    ax.axvline(0.0, color=TRIAL_END_COLOR, ls="--", lw=0.8, alpha=0.7,
               zorder=0, clip_on=False)


def _finish_axes(ax):
    _strip_box(ax)
    ax.tick_params(labelsize=FONT_SIZE_TICK)


def _shared_ylabel(ax_bottom, label, hspace):
    """One y-label centred across a two-row column, hung on the bottom row's
    axes. ``hspace`` is the GridSpec gap between the rows, in axes heights."""
    ax_bottom.set_ylabel(label)
    ax_bottom.yaxis.set_label_coords(-0.24, 1.0 + hspace / 2.0)


def _draw_position_traces(ax, trials, indices, colors=None):
    """Mean-subtracted eye signal over time for the listed trials. With
    ``colors`` each trial gets its own color (the sample panel); without,
    all are drawn thin in the trial color (the all-trials panel)."""
    for k, index in enumerate(indices):
        trial = trials[index]
        signal = _eye_signal(trial["x"], trial["y"])
        if colors is None:
            ax.plot(trial["t"], signal - signal.mean(), color=TRIAL_COLOR, lw=0.4, alpha=0.6)
        else:
            ax.plot(trial["t"], signal - signal.mean(), color=colors[k], lw=0.9)
    _mark_trial_end(ax)
    _finish_axes(ax)


def _draw_duration_hist(ax, durations, color):
    durations = np.asarray(durations, dtype=float)
    ax.hist(durations, bins=DURATION_BIN_EDGES, color=color, alpha=0.7, edgecolor="none")
    ax.set_xlim(0, 12)
    ax.set_ylabel("Count")
    _finish_axes(ax)
    _limit_ticks(ax, x=False)
    median = np.median(durations)
    ### Two decimals for short trials, fewer once the value reaches seconds,
    ### so 0.65 s and 10.98 s both read naturally.
    label = f"{median:.2f}" if median < 2 else f"{median:.1f}" if median < 10 else f"{median:.0f}"
    ### In whichever top corner the bars are not: failures pile up at the
    ### timeout on the right, everything else sits on the left.
    corner = "upper left" if median > DURATION_BIN_EDGES[-1] / 2 else "upper right"
    _annotate_n(ax, f"Median:\n{label} s", loc=corner)


def _draw_fixation_cdf(ax, trial_fixations, iti_fixations):
    for durations, color in ((iti_fixations, ITI_COLOR), (trial_fixations, TRIAL_COLOR)):
        ordered = np.sort(durations)
        ax.plot(ordered, np.arange(1, ordered.size + 1) / ordered.size, color=color, lw=1.2)
    ax.set_xlim(0, 1.5)
    ax.set_ylim(0, 1)
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_ylabel("CDF")
    _finish_axes(ax)


def _draw_distance_samples(ax, trials, indices):
    indices = [index for index in indices if index < len(trials)]
    for index, color in zip(indices, FEEDBACK_SAMPLE_COLORS):
        ax.plot(trials[index]["t"], trials[index]["distance"], color=color, lw=0.9)
    ax.axhline(0.0, color=ZERO_LINE_COLOR, lw=0.8, zorder=0)
    _mark_trial_end(ax)
    ax.set_xlim(-4, 2)
    ax.set_ylim(-2, 6)
    ax.set_xticks([-4, -2, 0, 2])
    ax.set_yticks([-2, 0, 2, 4, 6])
    _finish_axes(ax)
    _annotate_n(ax, f"n = {len(indices)}", loc="upper right")


def _draw_distance_overview(ax, trials, color):
    t_common = np.linspace(-12, 2, 600)
    ax.plot(t_common, resample_distance(trials, t_common).T, color=color, lw=0.5, alpha=0.35)
    ax.axhline(0.0, color=ZERO_LINE_COLOR, lw=0.8, zorder=0)
    _mark_trial_end(ax)
    ax.set_xlim(-12, 2)
    ax.set_ylim(-2, 8)
    ax.set_xticks([-12, -8, -4, 0, 2])
    ax.set_yticks([0, 4, 8])
    _finish_axes(ax)


def _draw_population_panel(ax, population, key, rng):
    """One of Panel G's two columns: a marker per session, grouped by animal,
    plus the mean +/- SD of each animal's standard-criterion sessions."""
    animals = sorted({session["animal_id"] for session in population})
    for position, animal in enumerate(animals, start=1):
        for criterion_ms, style in CRITERION_STYLE.items():
            values = np.array([session[key] for session in population
                               if session["animal_id"] == animal
                               and session["criterion_ms"] == criterion_ms])
            if values.size == 0:
                continue
            jitter = (rng.random(values.size) - 0.5) * JITTER_WIDTH
            ax.plot(position + jitter, values, ls="none", marker=style["marker"],
                    color=style["color"], markersize=4, markeredgewidth=0)
            ### Only the standard criterion has enough sessions for a mean;
            ### the 400 and 700 ms criteria are a single session per animal.
            if criterion_ms == STANDARD_CRITERION_MS and values.size > 1:
                ax.errorbar(position, values.mean(), yerr=values.std(ddof=1),
                            fmt="o", color="k", markersize=4.5, lw=1.2,
                            capsize=3, capthick=1.2, zorder=3)
    ax.set_xlim(0.5, len(animals) + 0.5)
    ax.set_xticks(range(1, len(animals) + 1))
    ax.set_xticklabels(animals)
    _finish_axes(ax)


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

def build_figure(results: dict):
    _apply_paper_style()

    ### Authored at its FINAL printed size, the same double-column width as
    ### Figure 3, so the point sizes on the two figures are literally equal.
    ### Rescaling this figure in Illustrator breaks that; change these
    ### instead.
    FIGURE_WIDTH_IN = 7.2
    FIGURE_HEIGHT_IN = 7.6

    ### The left column of the top two rows is deliberately empty: it is
    ### where the task schematics (Panels A and D) are placed by hand.
    SCHEMATIC_WIDTH = 1.0
    ROW_WIDTH_RATIOS = [SCHEMATIC_WIDTH, 2.35, 0.62]
    ROW_WSPACE = 0.32
    PAIR_HSPACE = 0.5   # gap between the two stacked rows of every panel

    fig = plt.figure(figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN))
    gs_main = fig.add_gridspec(3, 1, height_ratios=[1.0, 1.0, 0.5], hspace=0.42,
                               left=0.05, right=0.98, top=0.95, bottom=0.06)

    # --- Row 1: [space for Panel A] + Panel B (cued examples) + Panel C (CDFs) ---
    gs_top = gs_main[0].subgridspec(1, 3, width_ratios=ROW_WIDTH_RATIOS, wspace=ROW_WSPACE)
    gs_b = gs_top[0, 1].subgridspec(2, 3, width_ratios=[1.15, 1.0, 0.5],
                                    wspace=0.42, hspace=PAIR_HSPACE)
    gs_c = gs_top[0, 2].subgridspec(2, 1, hspace=PAIR_HSPACE)

    for row, session in enumerate(results["cued"]):
        ax_sample = fig.add_subplot(gs_b[row, 0])
        ax_overview = fig.add_subplot(gs_b[row, 1])
        ax_hist = fig.add_subplot(gs_b[row, 2])
        ax_cdf = fig.add_subplot(gs_c[row, 0])
        trials = session["trials"]
        is_bottom = row == len(results["cued"]) - 1

        _draw_position_traces(ax_sample, trials, session["sample_trials"],
                              colors=session["sample_colors"])
        ax_sample.set_xlim(-2.5, 0)
        ax_sample.set_ylim(-3, 3)
        ax_sample.set_xticks([-2, -1, 0])
        ax_sample.set_yticks([-3, 0, 3])
        _annotate_n(ax_sample, f"n = {len(session['sample_trials'])}", loc="upper left")

        overview = session["overview_trials"]
        overview = range(len(trials)) if overview is None else overview
        _draw_position_traces(ax_overview, trials, overview)
        ax_overview.set_xlim(-12, 0)
        ax_overview.set_ylim(-4.5, 4.5)
        ax_overview.set_xticks([-12, -8, -4, 0])
        ax_overview.set_yticks([-3, 0, 3])
        n_shown = (f"n = {len(overview)}" if len(overview) == len(trials)
                   else f"n = {len(overview)} of {len(trials)}")
        _annotate_n(ax_overview, n_shown, loc="upper left")
        ax_overview.set_title(f"Fixation training: {session['criterion_ms']} ms",
                              fontweight="bold")

        _draw_duration_hist(ax_hist, session["durations"], TRIAL_COLOR)
        ax_hist.set_xticks([0, 6, 12])

        _draw_fixation_cdf(ax_cdf, session["trial_fixations"], session["iti_fixations"])

        if row == 0:
            _panel_letter(ax_sample, "B")
            _panel_letter(ax_cdf, "C")
            ### Direct labels in the line colors rather than a legend box,
            ### which would cover a third of a panel this narrow.
            ax_cdf.text(0.98, 0.34, "Trial", color=TRIAL_COLOR, fontweight="bold",
                        ha="right", va="bottom", transform=ax_cdf.transAxes,
                        fontsize=FONT_SIZE_LABEL)
            ax_cdf.text(0.98, 0.20, "ITI", color=ITI_COLOR, fontweight="bold",
                        ha="right", va="bottom", transform=ax_cdf.transAxes,
                        fontsize=FONT_SIZE_LABEL)
        if is_bottom:
            _shared_ylabel(ax_sample, "Eye position (deg)", PAIR_HSPACE)
            ax_sample.set_xlabel("Time to trial end (s)")
            ax_overview.set_xlabel("Time to trial end (s)")
            ax_hist.set_xlabel("Trial dur (s)")
            ax_cdf.set_xlabel("Fixation dur (s)")

    # --- Row 2: [space for Panel D] + Panel E (distance traces) + Panel F (durations) ---
    example = results["example"]
    n_all = len(example["trials"])
    gs_mid = gs_main[1].subgridspec(1, 3, width_ratios=ROW_WIDTH_RATIOS, wspace=ROW_WSPACE)
    gs_e = gs_mid[0, 1].subgridspec(2, 2, width_ratios=[1.0, 1.55],
                                    wspace=0.28, hspace=PAIR_HSPACE)
    gs_f = gs_mid[0, 2].subgridspec(2, 1, hspace=PAIR_HSPACE)

    outcome_rows = [
        ("Successes", example["successes"], FEEDBACK_SAMPLE_SUCCESSES, TRIAL_COLOR),
        ("Failures", example["failures"], FEEDBACK_SAMPLE_FAILURES, FAIL_COLOR),
    ]
    hist_axes = []
    for row, (label, trials, sample_indices, color) in enumerate(outcome_rows):
        ax_sample = fig.add_subplot(gs_e[row, 0])
        ax_overview = fig.add_subplot(gs_e[row, 1])
        ax_hist = fig.add_subplot(gs_f[row, 0])
        hist_axes.append(ax_hist)

        _draw_distance_samples(ax_sample, trials, sample_indices)
        _draw_distance_overview(ax_overview, trials, color)
        ax_overview.set_title(
            f"{label} (n = {len(trials)}/{n_all}, {100 * len(trials) / n_all:.0f}%)",
            color=color, fontweight="bold")
        _draw_duration_hist(ax_hist, [trial["duration"] for trial in trials], color)
        ax_hist.set_xticks([0, 10])

        if row == 0:
            _panel_letter(ax_sample, "E")
            _panel_letter(ax_hist, "F")
        else:
            _shared_ylabel(ax_sample, "Distance to target (deg)", PAIR_HSPACE)
            ax_sample.set_xlabel("Time to trial end (s)")
            ax_overview.set_xlabel("Time to trial end (s)")
            ax_hist.set_xlabel("Trial dur (s)")

    ### Both histograms on one count axis, so the single tall failure bar at
    ### the timeout is read against the same scale as the successes.
    y_top = max(ax.get_ylim()[1] for ax in hist_axes)
    for ax in hist_axes:
        ax.set_ylim(0, y_top)
        _limit_ticks(ax, x=False)

    # --- Row 3: Panel G (population), under Panels E and F ---
    gs_bottom = gs_main[2].subgridspec(
        1, 5, width_ratios=[SCHEMATIC_WIDTH, 0.95, 0.25, 0.95, 0.82], wspace=ROW_WSPACE)
    ax_rate = fig.add_subplot(gs_bottom[0, 1])
    ax_duration = fig.add_subplot(gs_bottom[0, 3])
    population = results["population"]
    ### Seeded, so the jitter -- and therefore the saved file -- is the same
    ### on every run.
    rng = np.random.default_rng(0)

    _draw_population_panel(ax_rate, population, "success_rate", rng)
    ax_rate.set_ylim(0, 100)
    ax_rate.set_yticks([0, 50, 100])
    ax_rate.set_ylabel("% trials")
    ax_rate.set_title("Success rate", fontweight="bold")
    _panel_letter(ax_rate, "G")

    _draw_population_panel(ax_duration, population, "median_success_duration", rng)
    ax_duration.set_ylim(0, 11)
    ax_duration.set_yticks([0, 4, 8])
    ax_duration.set_ylabel("Median dur (s)")
    ax_duration.set_title("Trial duration\n(successes)", fontweight="bold")

    for k, criterion_ms in enumerate(sorted(CRITERION_STYLE)):
        ax_duration.text(1.08, 0.95 - 0.14 * k, f"{criterion_ms} ms",
                         color=CRITERION_STYLE[criterion_ms]["color"], fontweight="bold",
                         ha="left", va="top", transform=ax_duration.transAxes,
                         fontsize=FONT_SIZE_LABEL)

    return fig


### Guarded so this module can be imported (by tests, or by another figure
### script wanting one of its helpers) without re-running the whole analysis
### and writing files as a side effect of the import.
if __name__ == "__main__":
    results = run_analysis()
    print_summary(results)
    fig = build_figure(results)
    _save(fig, OUTPUT_STEM)
    plt.show()
