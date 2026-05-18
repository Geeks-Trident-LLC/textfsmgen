import json
import pytest
from textfsmgen.cli.shared_builder_cli import generate_or_save_config


def test_generate_config_prints_to_stdout(capsys):
    with pytest.raises(SystemExit) as exc:
        generate_or_save_config(
            builder_name="freeform",
            cfg_path="",
            params={"a": 1},
            snippet="hello",
            snippet_file="snippet.txt",
            sample_file="sample.txt",
            command="cmd",
            show="snippet",
            save="",
        )

    assert exc.value.code == 0  # success exit
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert data["params"] == {"a": 1}


def test_generate_config_saves_to_file(tmp_path, capsys):
    cfg_file = tmp_path / "cfg.json"

    with pytest.raises(SystemExit) as exc:
        generate_or_save_config(
            builder_name="freeform",
            cfg_path=str(cfg_file),
            params={"x": 2},
            snippet="abc",
            snippet_file="snippet.txt",
            sample_file="sample.txt",
            command="cmd",
            show="template",
            save="",
        )

    assert exc.value.code == 0
    assert cfg_file.exists()

    data = json.loads(cfg_file.read_text())
    assert data["params"] == {"x": 2}
    assert data["snippet"] == "abc"


def test_generate_config_fails_if_file_exists(tmp_path, capsys):
    cfg_file = tmp_path / "cfg.json"
    cfg_file.write_text("already here")

    with pytest.raises(SystemExit) as exc:
        generate_or_save_config(
            builder_name="freeform",
            cfg_path=str(cfg_file),
            params={"x": 2},
        )

    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "already exists" in out
