from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from eyehead.io import load_session_data
from utils.session_loader import SessionConfig


def _config(tmp_path: Path) -> SessionConfig:
    return SessionConfig(session_id="test", folder_path=tmp_path, animal_id="animal")


def _write_required(tmp_path: Path) -> None:
    # Every CSV needs at least two data rows: np.genfromtxt returns a 1-D
    # array for a single row, and load_session_data indexes columns as 2-D.
    (tmp_path / "ellipse_center_xy.csv").write_text("frame,time,x,y\n1,0,0,0\n2,1,0,0\n")
    (tmp_path / "origin_of_eyecoordinate.csv").write_text(
        "frame,time,lx,ly,rx,ry\n1,0,0,0,0,0\n2,1,0,0,0,0\n"
    )


def test_prefers_prefixed_file(tmp_path: Path) -> None:
    _write_required(tmp_path)
    (tmp_path / "animal_camera.csv").write_text("frame,time\n1,0\n3,1\n")
    (tmp_path / "camera.csv").write_text("frame,time\n2,0\n4,1\n")
    data = load_session_data(_config(tmp_path))
    assert data.camera is not None
    assert data.camera[0][0] == 1.0


def test_falls_back_to_unprefixed(tmp_path: Path) -> None:
    _write_required(tmp_path)
    (tmp_path / "camera.csv").write_text("frame,time\n5,0\n6,1\n")
    data = load_session_data(_config(tmp_path))
    assert data.camera is not None
    assert data.camera[0][0] == 5.0
