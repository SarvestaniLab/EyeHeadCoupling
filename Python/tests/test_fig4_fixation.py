"""Correctness checks for the Fig 4 fixation figure script.

``Fig4_fixation.py`` is a Python port of the MATLAB scripts that produced
the published figure, so the thing most worth guarding is that the port
keeps producing the published numbers. Three kinds of test live here:

1. Pure-logic tests of the ported algorithms -- fixation detection and the
   trial builders for both tasks -- on small synthetic inputs where the
   right answer is known by construction. These need no data.

2. Regression tests that re-run the analysis on the real sessions and check
   the numbers the paper reports (trial counts, medians, fixation counts,
   success rates). Those values were verified, to the last sample, against
   the data stored in the original MATLAB ``.fig`` files. They skip cleanly
   when the data drive is not mounted.

3. A smoke test that the composite figure builds with the expected panels.

Runnable either way::

    pytest Python/tests/test_fig4_fixation.py
    python Python/tests/test_fig4_fixation.py
"""
from pathlib import Path
from unittest import SkipTest
import sys

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")  # never open a window from a test
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).resolve().parents[1]))

from paper_figures import Fig4_fixation as fig4


# ---------------------------------------------------------------------------
# 1. Pure logic
# ---------------------------------------------------------------------------

def _steady(level: float, n: int) -> np.ndarray:
    """``n`` samples hovering at ``level``: a stable eye, with enough wobble
    (0.1 deg) not to be mistaken for a dead signal."""
    return level + 0.1 * (np.arange(n) % 2)


def test_two_holds_split_by_a_saccade_are_two_fixations() -> None:
    t = np.arange(200) * 0.01
    signal = np.r_[_steady(0.0, 100), _steady(10.0, 100)]
    starts, ends = fig4.find_fixation_segments(t, signal)
    assert (starts, ends) == ([0, 100], [99, 199])
    assert np.allclose(fig4.fixation_durations(t, signal), [0.99, 0.99])


def test_small_shift_still_ends_a_fixation() -> None:
    """A 1 deg step is smaller than a "saccade" (5 deg) but larger than the
    fixation range (0.6 deg). The merge step must not glue the two holds
    back together just because the movement between them was small."""
    t = np.arange(200) * 0.01
    signal = np.r_[_steady(0.0, 100), _steady(1.0, 100)]
    starts, ends = fig4.find_fixation_segments(t, signal)
    assert (starts, ends) == ([0, 100], [99, 199])


def test_hold_shorter_than_minimum_duration_is_dropped() -> None:
    t = np.arange(210) * 0.01
    signal = np.r_[_steady(0.0, 100), _steady(10.0, 10), _steady(20.0, 100)]
    starts, ends = fig4.find_fixation_segments(t, signal)
    assert (starts, ends) == ([0, 110], [99, 209]), (
        "the 0.09 s hold in the middle is under FIX_MIN_DURATION_S and must go"
    )


def test_dead_flat_signal_is_not_a_fixation() -> None:
    """A tracker dropout logs a constant value. It is perfectly "stable" but
    is not the eye holding still."""
    t = np.arange(200) * 0.01
    assert fig4.find_fixation_segments(t, np.full(200, 3.0)) == ([], [])


def test_empty_signal_has_no_fixations() -> None:
    assert fig4.find_fixation_segments(np.array([]), np.array([])) == ([], [])


def test_cued_trials_pair_each_trial_end_with_the_preceding_cue() -> None:
    eye_t = np.arange(0, 10, 0.1)
    eye_x = np.linspace(0, 1, eye_t.size)
    eye_y = np.zeros(eye_t.size)
    cue_t = np.array([1.0, 5.0])
    ### The first trial end (0.5 s) comes before any cue and must be skipped.
    eot_t = np.array([0.5, 2.0, 7.0])

    trials = fig4.build_cued_trials(eye_t, eye_x, eye_y, cue_t, eot_t)
    assert len(trials) == 2
    assert np.allclose([trial["duration"] for trial in trials], [1.0, 2.0])
    for trial in trials:
        ### Time runs up to trial end (t = 0), less the trimmed last 50 ms.
        assert trial["t"].max() <= -fig4.TRIAL_END_TRIM_S + 1e-9
        assert trial["t"].min() >= -trial["duration"] - 1e-9


def _feedback_frames(outcomes):
    """A minimal fixation-on-target session: one target per 10 s, the gaze
    marker sitting exactly on the target throughout."""
    n = len(outcomes)
    eye_t = np.arange(0, 10 * n + 5, 0.1)
    eye_df = pd.DataFrame(dict(timestamp=eye_t, green_x=0.4, green_y=0.0, diameter=0.2))
    target_df = pd.DataFrame(dict(timestamp=10.0 * np.arange(n) + 1.0,
                                  target_x=0.4, target_y=0.0, diameter=0.4))
    eot_df = pd.DataFrame(dict(timestamp=10.0 * np.arange(n) + 4.0,
                               trial_success=outcomes))
    return eot_df, eye_df, target_df


def test_feedback_success_is_the_highest_outcome_code() -> None:
    """Rig versions code a rewarded trial as 1 or as 2. Either way it is the
    highest code present, never a fixed number."""
    for outcomes, expected in (([0, 1, 1], [False, True, True]),
                               ([1, 2, 1], [False, True, False])):
        trials = fig4.build_feedback_trials(*_feedback_frames(outcomes))
        assert [trial["success"] for trial in trials] == expected


def test_feedback_distance_is_edge_to_edge_and_runs_past_trial_end() -> None:
    trials = fig4.build_feedback_trials(*_feedback_frames([1, 0]))
    trial = trials[0]
    assert np.isclose(trial["duration"], 3.0)
    ### Marker centred on the target: the gap between their edges is minus
    ### the sum of the two radii, in degrees.
    expected = -(0.4 / 2 + 0.2 / 2) * fig4.FEEDBACK_DEG_PER_UNIT
    assert np.allclose(trial["distance"], expected)
    assert np.isclose(trial["t"].max(), fig4.POST_TRIAL_S, atol=0.1)


def test_resampled_distance_is_nan_outside_the_trial() -> None:
    trial = dict(t=np.array([-2.0, -1.0, 0.0]), distance=np.array([4.0, 2.0, 0.0]))
    t_common = np.array([-3.0, -1.5, 0.0, 1.0])
    resampled = fig4.resample_distance([trial], t_common)[0]
    assert np.isnan(resampled[0]) and np.isnan(resampled[3])
    assert np.allclose(resampled[1:3], [3.0, 0.0])


def test_configured_sample_trials_are_distinct() -> None:
    """A repeated index would silently draw one trial twice."""
    for session in fig4.CUED_SESSIONS:
        assert len(set(session["sample_trials"])) == len(session["sample_trials"])
        assert len(session["sample_colors"]) == len(session["sample_trials"])
        if session["overview_trials"] is not None:
            assert len(set(session["overview_trials"])) == len(session["overview_trials"])
    for indices in (fig4.FEEDBACK_SAMPLE_SUCCESSES, fig4.FEEDBACK_SAMPLE_FAILURES):
        assert len(set(indices)) == len(indices)


# ---------------------------------------------------------------------------
# 2. The published numbers, re-derived from the real sessions
# ---------------------------------------------------------------------------

_RESULTS = None


def _results_or_skip() -> dict:
    """Run the analysis once and share it between the tests below."""
    global _RESULTS
    if fig4.EYE_SIGNAL != "radial":
        raise SkipTest("published numbers only hold for EYE_SIGNAL = 'radial'")
    data_root = fig4.paper_manifest.data_root()
    if not data_root.exists():
        raise SkipTest(f"data drive not available: {data_root}")
    if _RESULTS is None:
        _RESULTS = fig4.run_analysis()
    return _RESULTS


### criterion (ms) -> trials, median trial duration (s), fixations found
### within trials, fixations found within ITIs.
_PUBLISHED_CUED = {
    400: (127, 0.654, 242, 353),
    700: (262, 1.493, 774, 694),
}


def test_cued_sessions_reproduce_published_numbers() -> None:
    results = _results_or_skip()
    for session in results["cued"]:
        n_trials, median, n_trial_fix, n_iti_fix = _PUBLISHED_CUED[session["criterion_ms"]]
        label = f"{session['criterion_ms']} ms session"
        assert len(session["trials"]) == n_trials, f"{label}: trial count"
        assert abs(np.median(session["durations"]) - median) < 5e-4, f"{label}: median duration"
        assert session["trial_fixations"].size == n_trial_fix, f"{label}: within-trial fixations"
        assert session["iti_fixations"].size == n_iti_fix, f"{label}: ITI fixations"


def test_configured_trial_indices_exist() -> None:
    results = _results_or_skip()
    for session in results["cued"]:
        n = len(session["trials"])
        assert max(session["sample_trials"]) < n
        if session["overview_trials"] is not None:
            assert max(session["overview_trials"]) < n
    example = results["example"]
    assert max(fig4.FEEDBACK_SAMPLE_SUCCESSES) < len(example["successes"])
    assert max(fig4.FEEDBACK_SAMPLE_FAILURES) < len(example["failures"])


def test_feedback_example_reproduces_published_numbers() -> None:
    """"75 of 104 trials (72%)", median successful trial 2.7 s."""
    example = _results_or_skip()["example"]
    assert (len(example["successes"]), len(example["trials"])) == (75, 104)
    assert abs(example["median_success_duration"] - 2.655) < 5e-4
    ### Failures run to the timeout, so they must all outlast every success
    ### criterion by a wide margin.
    assert min(trial["duration"] for trial in example["failures"]) > 9.0


def test_feedback_population_reproduces_published_numbers() -> None:
    population = _results_or_skip()["population"]
    assert len(population) == 14
    ### Mean success rate (%) over each animal's 500 ms sessions.
    published_mean_rate = {"Tsh001": (6, 86.485), "Tsh002": (4, 73.820)}
    for animal, (n_sessions, mean_rate) in published_mean_rate.items():
        rates = [session["success_rate"] for session in population
                 if session["animal_id"] == animal
                 and session["criterion_ms"] == fig4.STANDARD_CRITERION_MS]
        assert len(rates) == n_sessions, f"{animal}: session count"
        assert abs(np.mean(rates) - mean_rate) < 5e-3, f"{animal}: mean success rate"


# ---------------------------------------------------------------------------
# 3. The figure
# ---------------------------------------------------------------------------

def test_figure_builds() -> None:
    """Smoke test: B is 2x3, C 2x1, E 2x2, F 2x1 and G 1x2 -- 16 axes."""
    results = _results_or_skip()
    fig = fig4.build_figure(results)
    try:
        assert len(fig.axes) == 16, f"expected 16 axes, got {len(fig.axes)}"
    finally:
        plt.close(fig)


# ---------------------------------------------------------------------------
# Minimal runner, so this file works without pytest installed
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import traceback

    tests = [
        (name, obj) for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    passed = skipped = failed = 0
    for name, fn in tests:
        try:
            fn()
        except SkipTest as exc:
            print(f"SKIP {name}: {exc}")
            skipped += 1
        except Exception:
            print(f"FAIL {name}")
            traceback.print_exc()
            failed += 1
        else:
            print(f"PASS {name}")
            passed += 1

    print(f"\n{passed} passed, {skipped} skipped, {failed} failed "
          f"(of {len(tests)})")
    sys.exit(1 if failed else 0)
