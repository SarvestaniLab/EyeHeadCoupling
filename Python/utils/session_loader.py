"""Utilities for loading session configuration data."""

from __future__ import annotations

import re
from contextlib import contextmanager
from dataclasses import MISSING, dataclass, field, fields
from pathlib import Path, PureWindowsPath
from typing import Any, Dict, Iterable, Iterator, List, Optional

import os
import yaml


@dataclass
class SessionConfig:
    """Configuration for a data collection session.

    Commonly used attributes are exposed directly on the dataclass while
    any additional ad-hoc values remain accessible via the ``params``
    dictionary.  Unknown attribute access falls back to ``params`` so that
    legacy fields continue to work.
    """

    session_id: str
    session_name: Optional[str] = None
    results_dir: Optional[Path] = None
    camera_side: Optional[str] = None
    eye_name: Optional[str] = None
    animal_name: Optional[str] = None
    animal_id: Optional[str] = None

    ttl_freq: Optional[float] = None
    calibration_factor: Optional[Any] = None
    folder_path: Optional[Path] = None
    params: Dict[str, Any] = field(default_factory=dict)

    def __getattr__(self, item: str) -> Any:  # pragma: no cover - simple delegation
        try:
            return self.params[item]
        except KeyError as exc:  # pragma: no cover - error path
            raise AttributeError(item) from exc


def _path_parts(p: str) -> List[str]:
    """Split a path string on both forward and backward slashes."""
    return [part for part in re.split(r"[/\\]", p) if part]


def _parse_animal_id_from_folder(folder_name: str) -> Optional[str]:
    """Extract animal_id from a folder name like 'Tsh001_2025-07-08T15_04_12'."""
    match = re.match(r"^(.+?)_\d{4}-\d{2}-\d{2}", folder_name)
    return match.group(1) if match else None


def _parse_animal_name_from_path(session_path: str) -> Optional[str]:
    """Extract animal_name from a session path whose parent folder is like 'TSh01_Paris_server'."""
    parts = _path_parts(session_path)
    if len(parts) < 2:
        return None
    parent = parts[-2]
    stripped = re.sub(r"_server$", "", parent, flags=re.IGNORECASE)
    name_parts = stripped.split("_")
    return name_parts[-1] if len(name_parts) >= 2 else None


def _parse_date_from_path(session_path: str) -> Optional[str]:
    """Extract date string (YYYY-MM-DD) from a session path."""
    match = re.search(r"\d{4}-\d{2}-\d{2}", session_path)
    return match.group() if match else None


# ---------------------------------------------------------------------------
# Which manifest is in use
# ---------------------------------------------------------------------------
### Every function below reads sessions from one manifest file. By default
### that is ``session_manifest.yml`` at the repo root: the live list, which
### grows as experiments continue. Anything that must NOT move when that
### list grows -- the paper's figures -- points the loader at a frozen
### manifest of its own instead (``Python/paper_figures/paper_manifest.yml``),
### so the same pipeline code serves both without either disturbing the
### other.
DEFAULT_MANIFEST = Path(__file__).resolve().parent.parent.parent / "session_manifest.yml"

_active_manifest: Optional[Path] = None


def get_manifest_path() -> Path:
    """Path of the manifest the loader is currently reading.

    In order of priority: the manifest set by :func:`using_manifest`, then
    the ``EHC_MANIFEST`` environment variable, then ``session_manifest.yml``
    at the repo root.
    """
    if _active_manifest is not None:
        return _active_manifest
    env_path = os.environ.get("EHC_MANIFEST")
    return Path(env_path) if env_path else DEFAULT_MANIFEST


@contextmanager
def using_manifest(path: Path | str) -> Iterator[Path]:
    """Read sessions from ``path`` instead of the default manifest, for the
    duration of a ``with`` block::

        with using_manifest(PAPER_MANIFEST):
            config = load_session("Tsh002_2026-08-19T12_49_59")

    The previous manifest is restored on exit, even after an error, so one
    script (or test) switching manifests cannot leak into the next.
    """
    global _active_manifest
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")
    previous = _active_manifest
    _active_manifest = path
    try:
        yield path
    finally:
        _active_manifest = previous


def load_manifest() -> Dict[str, Any]:
    """Parsed contents of the manifest currently in use."""
    with get_manifest_path().open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _resolve_session_folder(folder: Optional[str], manifest: Dict[str, Any]) -> Optional[str]:
    """A session's folder as an absolute path.

    A manifest may give ``data_root`` once at the top and then list each
    ``session_path`` relative to it, so moving the data (or handing the
    manifest to someone with the data elsewhere) means editing one line.
    Paths that are already absolute are returned unchanged, so manifests
    without ``data_root`` behave exactly as before.
    """
    data_root = manifest.get("data_root")
    if not folder or not data_root:
        return folder
    if Path(folder).is_absolute() or PureWindowsPath(folder).is_absolute():
        return folder
    return str(Path(data_root) / folder)


def load_session(session_id: str) -> SessionConfig:
    """Load the configuration for ``session_id``.

    Parameters
    ----------
    session_id:
        Identifier of the session to load.

    Returns
    -------
    SessionConfig
        The configuration for the requested session.

    Raises
    ------
    KeyError
        If ``session_id`` is not present in the manifest in use (see
        :func:`get_manifest_path`).
    """

    manifest: Dict[str, Any] = load_manifest()

    # Extract global defaults for saccade configuration, if provided.
    global_saccade_cfg: Dict[str, Any] = manifest.get("saccade_config", {}) or {}
    default_max_interval: Optional[float] = manifest.get("max_interval_fixations")
    default_reward_contingency: Optional[Dict[str, Any]] = manifest.get("reward_contingency")
    default_experiment_type: Optional[str] = manifest.get("experiment_type")
    results_root = manifest.get("results_root")
    results_with_data: bool = bool(manifest.get("results_with_data", False))


    # The manifest may either contain a top-level ``sessions`` key or map
    # session identifiers directly to their configuration.  Support both
    # layouts for flexibility.
    sessions: Dict[str, Any] = manifest.get("sessions", manifest)

    try:
        data = sessions[session_id] or {}
    except KeyError as exc:
        raise KeyError(f"Unknown session id: {session_id}") from exc

    folder = _resolve_session_folder(
        data.get("folder_path") or data.get("session_path"), manifest
    )
    results = data.get("results_dir")
    if results is None and folder:
        if results_with_data:
            results = Path(folder) / "Results2"
        elif results_root:
            session_folder = Path(folder).name
            results = Path(results_root) / session_folder

    known_keys = {
        "session_name",
        "results_dir",
        "camera_side",
        "eye_name",
        "animal_name",
        "animal_id",
        "date",
        "ttl_freq",
        "calibration_factor",
        "folder_path",
        "session_path",
        "params",
    }

    session_params: Dict[str, Any] = data.get("params") or {}
    params = {k: v for k, v in data.items() if k not in known_keys}
    params.update(session_params)

    # Derive animal_id, animal_name, and date from session_path when not
    # explicitly provided in the manifest, so old code using these fields
    # continues to work without them being listed in the manifest.
    folder_name = _path_parts(folder)[-1] if folder else ""
    animal_id = data.get("animal_id") or _parse_animal_id_from_folder(folder_name)
    animal_name = data.get("animal_name") or _parse_animal_name_from_path(folder or "")
    if "date" not in params:
        derived_date = data.get("date") or _parse_date_from_path(folder or "")
        if derived_date:
            params["date"] = derived_date

    if "max_interval_fixations" not in params and default_max_interval is not None:
        params["max_interval_fixations"] = default_max_interval

    session_reward_contingency: Dict[str, Any] = session_params.get("reward_contingency", {})
    merged_reward_contingency = {**(default_reward_contingency or {}), **session_reward_contingency}
    if merged_reward_contingency:
        params["reward_contingency"] = merged_reward_contingency

    if "experiment_type" not in params and default_experiment_type is not None:
        params["experiment_type"] = default_experiment_type

    # Merge global saccade defaults with any session-specific overrides and
    # fill in missing keys from :class:`SaccadeConfig` defaults.
    session_saccade_cfg: Dict[str, Any] = session_params.get("saccade_config", {})
    merged_saccade_cfg = {**global_saccade_cfg, **session_saccade_cfg}

    try:  # Import locally to avoid circular dependency during module import.
        from eyehead.analysis import SaccadeConfig

        for f in fields(SaccadeConfig):
            if f.name not in merged_saccade_cfg:
                if f.default is not MISSING:
                    merged_saccade_cfg[f.name] = f.default
                elif f.default_factory is not MISSING:  # pragma: no cover - defensive
                    merged_saccade_cfg[f.name] = f.default_factory()
    except Exception:  # pragma: no cover - fallback if import fails
        pass

    params["saccade_config"] = merged_saccade_cfg

    return SessionConfig(
        session_id=session_id,
        session_name=data.get("session_name", session_id),
        results_dir=Path(results) if results else None,
        camera_side=data.get("camera_side"),
        eye_name=data.get("eye_name") or data.get("camera_side"),
        animal_name=animal_name,
        animal_id=animal_id,

        ttl_freq=data.get("ttl_freq"),
        calibration_factor=data.get("calibration_factor"),
        folder_path=Path(folder) if folder else None,
        params=params,
    )

def load_session_or_path(identifier: str) -> SessionConfig:
    """Load a session by manifest ID, or fall back to a direct folder path.

    Parameters
    ----------
    identifier:
        Either a session ID present in ``session_manifest.yml``, or a direct
        filesystem path to a session folder.

    Returns
    -------
    SessionConfig
        The configuration for the requested session.
    """
    try:
        return load_session(identifier)
    except KeyError:
        folder = Path(identifier)
        if not folder.exists():
            raise
        return _build_config_from_folder(folder)


def _build_config_from_folder(folder: Path) -> SessionConfig:
    """Build a :class:`SessionConfig` directly from a folder path.

    Global defaults (``saccade_config``, ``max_interval_fixations``,
    ``results_root``) are still pulled from ``session_manifest.yml`` when
    available, but session-specific fields are derived from ``folder``
    instead of a manifest entry.
    """
    manifest_path = get_manifest_path()
    manifest: Dict[str, Any] = {}
    if manifest_path.exists():
        with manifest_path.open("r", encoding="utf-8") as fh:
            manifest = yaml.safe_load(fh) or {}

    global_saccade_cfg: Dict[str, Any] = manifest.get("saccade_config", {}) or {}
    default_max_interval: Optional[float] = manifest.get("max_interval_fixations")
    default_reward_contingency: Optional[Dict[str, Any]] = manifest.get("reward_contingency")
    default_experiment_type: Optional[str] = manifest.get("experiment_type")
    results_root = manifest.get("results_root")
    if results_root and not Path(results_root).is_absolute():
        results_root = manifest_path.parent / results_root
    results_with_data: bool = bool(manifest.get("results_with_data", False))
    sessions: Dict[str, Any] = manifest.get("sessions", {}) or {}

    folder_name = folder.name
    animal_id = _parse_animal_id_from_folder(folder_name)
    animal_name = _parse_animal_name_from_path(str(folder))
    date_str = _parse_date_from_path(str(folder))
    if results_with_data or not results_root:
        results_dir = folder / "Results2"
    else:
        results_dir = Path(results_root) / folder_name

    # ttl_freq/calibration_factor/camera_side describe the rig's fixed
    # hardware setup rather than anything derivable from the folder itself,
    # so inherit them from another manifest entry for the same animal.
    ttl_freq = calibration_factor = camera_side = eye_name = None
    if animal_id:
        for other_data in sessions.values():
            if not isinstance(other_data, dict):
                continue
            other_folder = other_data.get("folder_path") or other_data.get("session_path") or ""
            other_animal_id = other_data.get("animal_id") or _parse_animal_id_from_folder(
                _path_parts(other_folder)[-1] if other_folder else ""
            )
            if other_animal_id == animal_id:
                ttl_freq = other_data.get("ttl_freq", ttl_freq)
                calibration_factor = other_data.get("calibration_factor", calibration_factor)
                camera_side = other_data.get("camera_side", camera_side)
                eye_name = other_data.get("eye_name", eye_name)

    if ttl_freq is None or calibration_factor is None:
        raise ValueError(
            f"Could not determine ttl_freq/calibration_factor for '{folder_name}': "
            f"no existing manifest entry for animal_id={animal_id!r} to inherit rig "
            f"calibration from. Add this session (or another session for the same "
            f"animal) to session_manifest.yml first."
        )

    params: Dict[str, Any] = {}
    if date_str:
        params["date"] = date_str
    if default_max_interval is not None:
        params["max_interval_fixations"] = default_max_interval
    if default_reward_contingency is not None:
        params["reward_contingency"] = default_reward_contingency
    if default_experiment_type is not None:
        params["experiment_type"] = default_experiment_type

    merged_saccade_cfg = dict(global_saccade_cfg)


    try:  # Import locally to avoid circular dependency during module import.
        from eyehead.analysis import SaccadeConfig

        for f in fields(SaccadeConfig):
            if f.name not in merged_saccade_cfg:
                if f.default is not MISSING:
                    merged_saccade_cfg[f.name] = f.default
                elif f.default_factory is not MISSING:  # pragma: no cover - defensive
                    merged_saccade_cfg[f.name] = f.default_factory()
    except Exception:  # pragma: no cover - fallback if import fails
        pass
    params["saccade_config"] = merged_saccade_cfg

    return SessionConfig(
        session_id=folder_name,
        session_name=folder_name,
        results_dir=results_dir,
        camera_side=camera_side,
        eye_name=eye_name or camera_side,
        animal_name=animal_name,
        animal_id=animal_id,
        ttl_freq=ttl_freq,
        calibration_factor=calibration_factor,
        folder_path=folder,
        params=params,
    )

_DATA_DIR = Path(
    os.environ.get(
        "EHC_DATA_DIR", Path(__file__).resolve().parent.parent.parent / "data"
    )
)


def _session_dirs(base: Path | None = None) -> Iterable[Path]:
    """Yield session directories located under ``base``.

    Parameters
    ----------
    base:
        Optional path to search. When omitted, the module level ``_DATA_DIR``
        is used. The directory is created lazily if it does not exist.
    """
    root = base or _DATA_DIR
    if not root.exists():
        return []
    return [p for p in root.iterdir() if p.is_dir()]


def list_sessions() -> List[str]:
    """Return the names of all available sessions.

    Returns
    -------
    list of str
        Sorted list of session directory names. If the data directory is
        missing, an empty list is returned.
    """
    return sorted(p.name for p in _session_dirs())


def list_sessions_by_type(experiment_type: str) -> List[str]:
    """Return sessions whose name matches ``experiment_type``.

    Parameters
    ----------
    experiment_type:
        Prefix identifying an experiment class. Session names are expected to
        have the form ``"{experiment_type}_<details>"``. The comparison is
        case-insensitive.

    Returns
    -------
    list of str
        Sorted list of session names beginning with ``experiment_type``.
    """
    prefix = f"{experiment_type.lower()}_"
    return sorted(
        name for name in list_sessions() if name.lower().startswith(prefix)
    )


def list_sessions_from_manifest(
    experiment_type: Optional[str] = None,
    *,
    match_prefix: bool = False,
    animal_name: Optional[str] = None,
) -> List[str]:
    """Return session IDs from the manifest filtered by metadata.

    Parameters
    ----------
    experiment_type:
        Optional experiment type to filter sessions by. When provided the
        value is compared directly against the ``"experiment_type"`` field of
        each manifest entry.
    match_prefix:
        When ``True`` and ``experiment_type`` is provided, include sessions whose
        ``experiment_type`` begins with ``experiment_type`` (case-insensitive).
    animal_name:
        Optional animal name to filter sessions by. When provided, only
        sessions whose manifest entry specifies the same ``"animal_name"`` (case
        insensitive) are returned.

    Returns
    -------
    list of str
        Sorted list of session identifiers that satisfy the requested
        filtering criteria. If the manifest file is missing or empty an empty
        list is returned.
    """

    manifest_path = get_manifest_path()

    try:
        with manifest_path.open("r", encoding="utf-8") as fh:
            manifest: Dict[str, Any] = yaml.safe_load(fh) or {}
    except FileNotFoundError:  # pragma: no cover - defensive programming
        return []

    sessions: Dict[str, Any] = manifest.get("sessions", manifest)
    exp_type_lower = experiment_type.lower() if experiment_type else None
    animal_name_lower = animal_name.lower() if animal_name else None

    matched_sessions: List[str] = []
    for session_id, meta in sessions.items():
        if not isinstance(meta, dict):  # pragma: no cover - defensive
            continue

        if experiment_type:
            meta_type = meta.get("experiment_type")
            if not meta_type:
                continue
            if match_prefix:
                if not meta_type.lower().startswith(exp_type_lower):
                    continue
            elif meta_type != experiment_type:
                continue

        if animal_name_lower is not None:
            meta_animal = meta.get("animal_name") or _parse_animal_name_from_path(
                meta.get("session_path") or meta.get("folder_path") or ""
            )
            if not meta_animal or meta_animal.lower() != animal_name_lower:
                continue

        matched_sessions.append(session_id)

    return sorted(matched_sessions)


__all__ = [
    "SessionConfig",
    "DEFAULT_MANIFEST",
    "get_manifest_path",
    "using_manifest",
    "load_manifest",
    "load_session",
    "load_session_or_path",
    "_build_config_from_folder",
    "list_sessions",
    "list_sessions_by_type",
    "list_sessions_from_manifest",
]
