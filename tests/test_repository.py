import pytest
from core.db import Repository


@pytest.fixture
def repo(tmp_path):
    return Repository(url=f"sqlite:///{tmp_path/'t.db'}", data_dir=tmp_path)


def _setup(repo):
    pid = repo.create_project("demo")
    did = repo.add_dataset(pid, "a.csv", b"x,y\n1,2\n", 1, 2)
    return pid, did


def test_versions_increment_and_revert_is_non_destructive(repo):
    pid, did = _setup(repo)
    v1 = repo.save_version(pid, did, "classification", "y", [{"op": "drop_duplicates", "params": {}}],
                           {"scaler": "standard"}, [{"name": "KNN", "params": {}}])
    repo.record_run(v1, [{"model": "KNN", "type": "classical", "accuracy": 0.9, "fit_time_s": 0.1}])
    v2 = repo.save_version(pid, did, "classification", "y", [], {"scaler": "none"},
                           [{"name": "KNN", "params": {}}], parent_id=v1)
    v3 = repo.revert_to(v1)
    h = repo.history(pid)
    assert [x["version_no"] for x in h] == [3, 2, 1]
    new = repo.get_version(v3)
    old = repo.get_version(v1)
    assert new["parent_id"] == v1 and new["cleaning_steps"] == old["cleaning_steps"]
    assert repo.get_version(v1)["optimization"] == {"scaler": "standard"}  # untouched
    assert repo.results_for(v1)[0]["accuracy"] == 0.9


def test_compare_reports_settings_diff(repo):
    pid, did = _setup(repo)
    a = repo.save_version(pid, did, "classification", "y", [], {"scaler": "standard"}, [])
    b = repo.save_version(pid, did, "classification", "y", [], {"scaler": "none"}, [])
    assert "optimization" in repo.compare(a, b)["settings_diff"]


def test_delete_dataset_removes_file_and_versions(repo, tmp_path):
    pid, did = _setup(repo)
    repo.save_version(pid, did, "classification", "y", [], {}, [])
    repo.delete_dataset(did)
    assert repo.history(pid) == []
    assert not list((tmp_path / "uploads").glob("*.csv"))
