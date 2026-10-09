from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from eyehead.io import load_session_data
from utils.session_loader import SessionConfig


def test_end_of_trial_arrays_present(tmp_path: Path) -> None:
    # Every CSV needs at least two data rows: np.genfromtxt returns a 1-D
    # array for a single row, and load_session_data indexes columns as 2-D.
    end = tmp_path / "end_of_trial.csv"
    end.write_text(
        "frame,time,stim_dir,eye_dir,torsion,success\n"
        "1,0.1,90,100,0.2,1\n"
        "7,2.1,270,80,0.1,0\n"
    )
    ell = tmp_path / "ellipse_center_xy.csv"
    ell.write_text("frame,time,x,y\n1,0,0,0\n2,1,0,0\n")
    origin = tmp_path / "origin_of_eyecoordinate.csv"
    origin.write_text("frame,time,lx,ly,rx,ry\n1,0,0,0,0,0\n2,1,0,0,0,0\n")

    data = load_session_data(SessionConfig(session_id="test", folder_path=tmp_path))
    assert data.end_of_trial_frame is not None
    assert data.trial_success is not None
    assert list(data.end_of_trial_frame) == [1, 7]
    assert list(data.trial_success) == [1, 0]
