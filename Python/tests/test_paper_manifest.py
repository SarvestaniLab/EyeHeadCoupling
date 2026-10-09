"""Checks for the paper manifest and the manifest switch in the session loader.

``Python/paper_figures/paper_manifest.yml`` freezes the sessions, settings
and folders behind the paper's figures, so the live ``session_manifest.yml``
can keep changing for ongoing experiments. That only works if three things
hold, and each has a test here:

1. The paper manifest is internally consistent: every session a figure names
   is defined, and every figure's population has sessions.

2. Switching manifests is contained. ``using_manifest`` must hand the
   default manifest back when its ``with`` block ends, even after an error,
   or one figure script would silently redirect everything run after it.

3. The freeze is enforced, not just declared: Figure 3 refuses a population
   cache holding any other set of sessions than the paper manifest's.

None of these needs the data drive except the last, which skips cleanly when
no cache is present.

Runnable either way::

    pytest Python/tests/test_paper_manifest.py
    python Python/tests/test_paper_manifest.py
"""
from pathlib import Path
from unittest import SkipTest
import sys
import tempfile

import matplotlib

matplotlib.use("Agg")  # never open a window from a test

sys.path.append(str(Path(__file__).resolve().parents[1]))

from paper_figures import paper_manifest
from utils import session_loader


# ---------------------------------------------------------------------------
# 1. The paper manifest itself
# ---------------------------------------------------------------------------

def test_paper_manifest_states_its_folders() -> None:
    manifest = paper_manifest.load()
    for key in ("data_root", "figures_root", "results_root", "figures", "sessions"):
        assert manifest.get(key), f"paper manifest is missing {key!r}"


def test_every_session_a_figure_names_is_defined() -> None:
    manifest = paper_manifest.load()
    defined = set(manifest["sessions"])
    for name, block in manifest["figures"].items():
        named = list(block.get("sessions", [])) + list(block.get("cued_sessions", []))
        if block.get("example_session"):
            named.append(block["example_session"])
        missing = [session_id for session_id in named if session_id not in defined]
        assert not missing, f"figure {name} names undefined sessions: {missing}"


def test_every_population_has_sessions() -> None:
    """A ``population`` entry names an experiment type. A typo there would
    not fail loudly on its own -- it would quietly pool zero sessions."""
    for name, block in paper_manifest.load()["figures"].items():
        if "population" in block:
            sessions = paper_manifest.sessions_of_type(block["population"])
            assert sessions, f"figure {name}: no sessions of type {block['population']!r}"


def test_example_session_belongs_to_its_population() -> None:
    for name, block in paper_manifest.load()["figures"].items():
        if "population" in block and block.get("example_session"):
            assert block["example_session"] in paper_manifest.sessions_of_type(block["population"]), (
                f"figure {name}: example_session is not one of its population's sessions"
            )


def test_session_paths_resolve_under_data_root() -> None:
    """Paper sessions give their folder relative to ``data_root``, so the
    data can move by editing one line."""
    data_root = paper_manifest.data_root()
    for session_id in paper_manifest.load()["sessions"]:
        folder = paper_manifest.session(session_id).folder_path
        assert folder.is_absolute(), f"{session_id}: folder was not resolved"
        assert data_root in folder.parents, f"{session_id}: {folder} is outside data_root"
        assert folder.name == session_id


def test_output_dir_accepts_relative_and_absolute() -> None:
    figures_root = Path(paper_manifest.load()["figures_root"])
    assert paper_manifest.output_dir("Fig3").parent == figures_root
    assert paper_manifest.output_dir("Fig4S").is_absolute()


# ---------------------------------------------------------------------------
# 2. Switching manifests is contained
# ---------------------------------------------------------------------------

def _write_manifest(folder: Path, name: str, body: str) -> Path:
    path = folder / name
    path.write_text(body, encoding="utf-8")
    return path


def test_default_manifest_is_the_live_one() -> None:
    assert session_loader.get_manifest_path() == session_loader.DEFAULT_MANIFEST
    assert session_loader.DEFAULT_MANIFEST.name == "session_manifest.yml"


def test_using_manifest_switches_and_restores() -> None:
    before = session_loader.get_manifest_path()
    with paper_manifest.frozen():
        assert session_loader.get_manifest_path() == paper_manifest.PAPER_MANIFEST
    assert session_loader.get_manifest_path() == before


def test_using_manifest_restores_after_an_error() -> None:
    before = session_loader.get_manifest_path()
    try:
        with paper_manifest.frozen():
            raise RuntimeError("analysis blew up mid-figure")
    except RuntimeError:
        pass
    assert session_loader.get_manifest_path() == before


def test_nested_switches_unwind_in_order() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        other = _write_manifest(Path(tmp), "other.yml", "sessions: {}\n")
        with paper_manifest.frozen():
            with session_loader.using_manifest(other):
                assert session_loader.get_manifest_path() == other
            assert session_loader.get_manifest_path() == paper_manifest.PAPER_MANIFEST
    assert session_loader.get_manifest_path() == session_loader.DEFAULT_MANIFEST


def test_missing_manifest_is_refused() -> None:
    try:
        with session_loader.using_manifest(Path("no_such_manifest.yml")):
            raise AssertionError("a manifest that does not exist was accepted")
    except FileNotFoundError:
        pass


def test_relative_session_path_joins_data_root_and_absolute_is_kept() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        elsewhere = tmp / "elsewhere" / "TSh09_Test_server" / "Tsh009_2030-01-02T03_04_05"
        manifest = _write_manifest(tmp, "m.yml", "\n".join([
            f"data_root: {tmp / 'data'}",
            "sessions:",
            "  Tsh009_2030-01-01T00_00_00:",
            "    session_path: TSh09_Test_server/Tsh009_2030-01-01T00_00_00",
            "  Tsh009_2030-01-02T03_04_05:",
            f"    session_path: {elsewhere}",
            "",
        ]))
        with session_loader.using_manifest(manifest):
            relative = session_loader.load_session("Tsh009_2030-01-01T00_00_00")
            absolute = session_loader.load_session("Tsh009_2030-01-02T03_04_05")
        assert relative.folder_path == tmp / "data" / "TSh09_Test_server" / "Tsh009_2030-01-01T00_00_00"
        assert absolute.folder_path == elsewhere
        ### The animal is still read off the folder names either way.
        assert relative.animal_id == "Tsh009" and relative.animal_name == "Test"


def test_manifest_without_data_root_is_unchanged() -> None:
    """The live manifest has no ``data_root``; its paths must be passed
    through exactly as written."""
    with tempfile.TemporaryDirectory() as tmp:
        manifest = _write_manifest(Path(tmp), "m.yml", "\n".join([
            "sessions:",
            "  Tsh009_2030-01-01T00_00_00:",
            "    session_path: some/relative/Tsh009_2030-01-01T00_00_00",
            "",
        ]))
        with session_loader.using_manifest(manifest):
            config = session_loader.load_session("Tsh009_2030-01-01T00_00_00")
        assert config.folder_path == Path("some/relative/Tsh009_2030-01-01T00_00_00")


# ---------------------------------------------------------------------------
# 3. The freeze is enforced
# ---------------------------------------------------------------------------

def test_fig3_refuses_a_cache_with_other_sessions() -> None:
    """If a run on the live manifest overwrote the population cache with a
    different set of sessions, Figure 3 must stop rather than draw them."""
    from paper_figures import Fig3_prosaccade as fig3

    try:
        fig3._load_population_cache(fig3.EXPERIMENT_TYPE)
    except FileNotFoundError as exc:
        raise SkipTest(f"no population cache available: {exc}")

    real = paper_manifest.sessions_of_type
    ### Pretend the paper manifest listed one session the cache lacks.
    paper_manifest.sessions_of_type = lambda *a, **k: real(*a, **k) + ["Tsh001_2099-01-01T00_00_00"]
    try:
        try:
            fig3._load_population_cache(fig3.EXPERIMENT_TYPE)
        except ValueError as exc:
            assert "Tsh001_2099-01-01T00_00_00" in str(exc)
        else:
            raise AssertionError("a cache not matching the paper manifest was accepted")
    finally:
        paper_manifest.sessions_of_type = real


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
