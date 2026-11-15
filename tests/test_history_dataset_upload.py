import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from rl import make_history_dataset as builder


@pytest.mark.parametrize("auth_status", [401, 403])
def test_retry_recovers_transient_errors_and_does_not_retry_auth(
    monkeypatch, auth_status
):
    sleeps = []
    monkeypatch.setattr(builder.time, "sleep", sleeps.append)
    request = httpx.Request("POST", "https://example.invalid/tasks")

    def error(status):
        return httpx.HTTPStatusError(
            "test failure", request=request, response=httpx.Response(status)
        )

    outcomes = iter([error(520), httpx.ConnectError("test transport failure"), "ok"])

    def operation():
        result = next(outcomes)
        if isinstance(result, Exception):
            raise result
        return result

    assert builder.retry_api(operation, "test") == "ok"
    assert sleeps == [1, 2]
    sleeps.clear()

    def unauthorized():
        raise error(auth_status)

    with pytest.raises(httpx.HTTPStatusError):
        builder.retry_api(unauthorized, "test")
    assert not sleeps


def test_upload_resumes_acknowledged_prefix_and_verifies_membership(
    tmp_path: Path, monkeypatch
):
    scenarios = builder.load_scenarios(builder.ROOT / "history" / "raw")
    built, manifest = builder.build_dataset(
        scenarios, counts=dict.fromkeys(builder.COUNTS, 6)
    )
    builder.write_exports(built, manifest, tmp_path)
    train_name = manifest["splits"]["train"]["dataset_name"]
    prefix = built["train"][:2]

    def task_id(task):
        return f"tsk_{task.env_params['seed']}"

    class FakeDatasets:
        def __init__(self):
            self.members = {train_name: [task_id(t) for t in prefix]}
            self.tasks = {task_id(t): t for t in prefix}
            self.added = {}

        def list(self):
            return [self.get(name) for name in self.members]

        def get(self, name):
            return SimpleNamespace(
                name=name, id=f"ds_{name}", task_count=len(self.members[name])
            )

        def create(self, name, **kwargs):
            self.members[name] = []
            return self.get(name)

        def add_tasks(self, name, *, tasks):
            self.added.setdefault(name, []).extend(tasks)
            ids = []
            for task in tasks:
                ident = task_id(task)
                self.tasks[ident] = task
                if ident not in self.members[name]:
                    self.members[name].append(ident)
                ids.append(ident)
            return ids

        def active_tasks(self, name):
            return [SimpleNamespace(id=ident) for ident in self.members[name]]

        def load_task(self, ident):
            return self.tasks[ident]

    fake = FakeDatasets()
    receipt = {
        "project": "vals-hackathon",
        "prefix": builder.PREFIX,
        "complete": False,
        "datasets": {
            "train": {
                "dataset_id": f"ds_{train_name}",
                "dataset_name": train_name,
                "sha256": manifest["splits"]["train"]["sha256"],
                "task_ids": [task_id(t) for t in prefix],
            }
        },
    }
    (tmp_path / "upload.json").write_text(json.dumps(receipt))
    monkeypatch.setattr(
        builder, "Client", lambda **kwargs: SimpleNamespace(datasets=fake)
    )
    uploaded = builder.upload_and_verify(built, manifest, tmp_path, "vals-hackathon")
    assert fake.added[train_name] == built["train"][2:]
    assert uploaded["complete"]
    assert all(
        r["verified_membership"] and r["task_count"] == 6
        for r in uploaded["datasets"].values()
    )
