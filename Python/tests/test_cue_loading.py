from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from eyehead.io import load_session_data
from utils.session_loader import SessionConfig


def test_cue_arrays_present(tmp_path: Path) -> None:
    # Every CSV needs at least two data rows: np.genfromtxt returns a 1-D
    # array for a single row, and load_session_data indexes columns as 2-D.
    cue = tmp_path / "cue.csv"
    cue.write_text("frame,time\n1,0.0\n2,2.0\n5,4.0\n")
    ell = tmp_path / "ellipse_center_xy.csv"
    ell.write_text("frame,time,x,y\n1,0,0,0\n2,1,0,0\n")
    origin = tmp_path / "origin_of_eyecoordinate.csv"
    origin.write_text("frame,time,lx,ly,rx,ry\n1,0,0,0,0,0\n2,1,0,0,0,0\n")
    data = load_session_data(SessionConfig(session_id="test", folder_path=tmp_path))
    assert data.cue_frame is not None
    assert data.cue_time is not None
