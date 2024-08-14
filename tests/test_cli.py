"""
Test command line
"""

import sys

import pytest

from workenv.cli import run

config_sample = """
_common:
  env:
    COMMON: value_common_{{project.name}}
  commands:
    open:
      run: xdg-open .
      env:
        PROJECT_NAME: "{{project.name}}"
project:
  path: /path/1
  env:
    PROJECT: value_project_{{project.name}}
  run: pwd
  commands:
    list:
      run: ls
"""


@pytest.fixture
def config_file(monkeypatch, tmp_path):
    file = tmp_path / "workenv_config.yml"
    monkeypatch.setenv("WORKENV_CONFIG_PATH", str(file))
    return file


def test_run_project(capsys, monkeypatch, config_file):
    config_file.write_text(config_sample)
    monkeypatch.setattr(sys, "argv", ["workenv", "project"])
    run()
    captured = capsys.readouterr()
    assert (
        captured.out
        == "\n".join(
            [
                "cd /path/1",
                "export COMMON=value_common_project",
                "export PROJECT=value_project_project",
                "pwd",
            ]
        )
        + "\n"
    )


def test_run_common_command(capsys, monkeypatch, config_file):
    config_file.write_text(config_sample)
    monkeypatch.setattr(sys, "argv", ["workenv", "project", "open"])
    run()
    captured = capsys.readouterr()
    assert (
        captured.out
        == "\n".join(
            [
                "cd /path/1",
                "export COMMON=value_common_project",
                "export PROJECT_NAME=project",
                "xdg-open .",
            ]
        )
        + "\n"
    )


def test_run_project_command(capsys, monkeypatch, config_file):
    config_file.write_text(config_sample)
    monkeypatch.setattr(sys, "argv", ["workenv", "project", "list"])
    run()
    captured = capsys.readouterr()
    assert (
        captured.out
        == "\n".join(
            [
                "cd /path/1",
                "export COMMON=value_common_project",
                "export PROJECT=value_project_project",
                "ls",
            ]
        )
        + "\n"
    )


# TODO:
def test_add_no_arguments():
    """
    Traceback (most recent call last):
      File "/home/radiac/work/projects/workenv/venv/bin/workenv", line 11, in <module>
        load_entry_point('workenv', 'console_scripts', 'workenv')()
      File "/home/radiac/work/projects/workenv/repo/workenv/cli.py", line 42, in run
        action_registry[action](config, actions, args)
      File "/home/radiac/work/projects/workenv/repo/workenv/actions.py", line 57, in add
        project_name, command_name = (args + [None])[0:2]
    ValueError: not enough values to unpack (expected 2, got 1)
    """
