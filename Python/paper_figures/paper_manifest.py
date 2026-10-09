"""Access to the paper manifest (``paper_manifest.yml``, next to this file).

The paper manifest is the frozen counterpart of the repo's live
``session_manifest.yml``: it lists exactly the sessions the paper's figures
use, the settings they were analysed with, and the folders to read from and
write to. Every figure script in this folder gets its sessions and paths
through this module, so nothing that happens to the live manifest (new
sessions for ongoing experiments, changed thresholds) can alter a figure.

Two kinds of use:

- Asking what the paper uses::

      fig = paper_manifest.figure("Fig4")        # that figure's block
      paper_manifest.session(fig["example_session"]).folder_path
      paper_manifest.sessions_of_type("fixation_on_target")
      paper_manifest.output_dir("Fig4")

- Running pipeline code against the paper's sessions. The pipeline
  (``prosaccade_session.main``, ``eyehead.load_session_data`` ...) looks
  sessions up through :mod:`utils.session_loader`; wrap the call so those
  lookups go to the paper manifest instead of the live one::

      with paper_manifest.frozen():
          data = load_session_data(load_session(session_id))

  or decorate a whole function with :func:`uses_paper_manifest`.
"""
from __future__ import annotations

import functools
from pathlib import Path, PureWindowsPath
from typing import Any, Dict, List

import yaml

from utils.session_loader import (
    SessionConfig,
    list_sessions_from_manifest,
    load_session,
    using_manifest,
)

PAPER_MANIFEST = Path(__file__).resolve().parent / "paper_manifest.yml"


def frozen():
    """Context manager: inside the ``with`` block, every session lookup made
    by the pipeline reads the paper manifest rather than the live one. The
    live manifest is back in force as soon as the block ends."""
    return using_manifest(PAPER_MANIFEST)


def uses_paper_manifest(func):
    """Decorator form of :func:`frozen`, for a function whose whole body
    should see the paper's sessions."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with frozen():
            return func(*args, **kwargs)
    return wrapper


def load() -> Dict[str, Any]:
    """The paper manifest, parsed."""
    with PAPER_MANIFEST.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def figure(name: str) -> Dict[str, Any]:
    """The ``figures: <name>`` block: which sessions that figure uses and
    where it saves."""
    figures = load().get("figures") or {}
    if name not in figures:
        raise KeyError(
            f"{PAPER_MANIFEST.name} has no entry for figure {name!r} "
            f"(it lists: {sorted(figures)})."
        )
    return figures[name]


def data_root() -> Path:
    """Folder holding the raw session folders."""
    return Path(load()["data_root"])


def results_root() -> Path:
    """Folder the pipeline writes per-session results and population caches
    to when it is run with the paper manifest."""
    return Path(load()["results_root"])


def output_dir(name: str) -> Path:
    """Folder figure ``name`` saves into. Its ``output_dir`` is taken
    relative to ``figures_root`` unless it is written as a full path."""
    manifest = load()
    out = str(figure(name)["output_dir"])
    if Path(out).is_absolute() or PureWindowsPath(out).is_absolute():
        return Path(out)
    return Path(manifest["figures_root"]) / out


def session(session_id: str) -> SessionConfig:
    """Configuration of one of the paper's sessions (folder, animal,
    settings). Extra keys such as ``fixation_ms`` are under ``.params``."""
    with frozen():
        return load_session(session_id)


def sessions_of_type(experiment_type: str, match_prefix: bool = False) -> List[str]:
    """IDs of every paper session of ``experiment_type``, sorted. This is
    what a figure's ``population`` entry expands to."""
    with frozen():
        return list_sessions_from_manifest(experiment_type, match_prefix=match_prefix)
