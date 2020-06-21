"""
Test workenv/config.py from_dict
"""
from pathlib import Path

from workenv.config import Command, Config, Project, var_pattern


def test_project_attributes__parsed_to_project():
    conf = Config()
    conf.loads(
        """
project:
  path: /path/1
  source:
  - /path/1/src/1
  - /path/1/src/2
  env:
    key: value
  run:
  - /path/1/run/1
  - /path/1/run/2
        """
    )

    assert list(conf.projects.keys()) == ["project"]

    project = conf.projects["project"]
    assert isinstance(project, Project)
    assert project.path == Path("/path/1")
    assert project.source == ["/path/1/src/1", "/path/1/src/2"]
    assert project.env == {"key": "value"}
    assert project.run == ["/path/1/run/1", "/path/1/run/2"]


def test_project_command__parsed_to_command():
    conf = Config()
    conf.loads(
        """
project:
  commands:
    command:
      path: /path/1/cmd/1
      source:
      - /path/1/cmd/1/src/1
      - /path/1/cmd/1/src/2
      run:
      - /path/1/cmd/1/run/1
      - /path/1/cmd/1/run/2
"""
    )

    assert list(conf.projects.keys()) == ["project"]

    project = conf.projects["project"]
    assert isinstance(project, Project)
    assert list(project.commands.keys()) == ["command"]

    project_command = project.commands["command"]
    assert isinstance(project_command, Command)
    assert project_command.path == Path("/path/1/cmd/1")
    assert project_command.source == ["/path/1/cmd/1/src/1", "/path/1/cmd/1/src/2"]
    assert project_command.run == ["/path/1/cmd/1/run/1", "/path/1/cmd/1/run/2"]


def test_command_without_path__inherits_from_project():
    conf = Config()
    conf.loads(
        """
project:
  path: /path/1
  commands:
    command:
        """
    )

    assert list(conf.projects.keys()) == ["project"]

    project = conf.projects["project"]
    assert isinstance(project, Project)
    assert project.path == Path("/path/1")
    assert project.commands["command"].path == Path("/path/1")


def test_command_without_path__inherits_path_from_project():
    conf = Config()
    conf.loads(
        """
project:
  path: /path/1
  commands:
    command:
        """
    )

    assert conf.projects["project"].commands["command"].path == Path("/path/1")


def test_command_without_path_and_source__inherits_source_from_project():
    conf = Config()
    conf.loads(
        """
project:
  source: /path/1/src/1
  commands:
    command:
        """
    )

    assert conf.projects["project"].commands["command"].source == ["/path/1/src/1"]


def test_command_without_env__inherits_env_from_project():
    conf = Config()
    conf.loads(
        """
project:
  env:
    key: value
  commands:
    command:
        """
    )

    assert conf.projects["project"].commands["command"].env == {"key": "value"}


def test_common_source__project_includes_common_source():
    conf = Config()
    conf.loads(
        """
_common:
  source: /path/1/src/1
project:
  source: /path/2/src/1
        """
    )

    assert conf.projects["project"].source == ["/path/1/src/1", "/path/2/src/1"]


def test_common_env__project_includes_common_env():
    conf = Config()
    conf.loads(
        """
_common:
  env:
    key1: value1
project:
  env:
    key2: value2
        """
    )

    assert conf.projects["project"].env == {
        "key1": "value1",
        "key2": "value2",
    }


def test_common_run__project_includes_common_run():
    conf = Config()
    conf.loads(
        """
_common:
  run: /path/1/run/1
project:
  run: /path/2/run/1
        """
    )

    assert conf.projects["project"].run == ["/path/1/run/1", "/path/2/run/1"]


def test_common_command__project_includes_common_command():
    conf = Config()
    conf.loads(
        """
_common:
  commands:
    open:
      run: xdg-open .
project:
  path: /path/1
        """
    )

    assert "open" in conf.projects["project"].commands
    assert conf.projects["project"].commands["open"].run == ["xdg-open ."]


def test_common_command__clone_to_project__path_correct():
    conf = Config()
    conf.loads(
        """
_common:
  commands:
    open:
      run: xdg-open .
project:
  path: /path/1
        """
    )

    project = conf.projects["project"]
    command = project.commands["open"]
    assert command.parent is not None
    assert command.parent != project

    clone = command.clone_to(project)
    assert clone.parent == project

    assert clone.path == Path("/path/1")


def test_common_command_env__clone_to_project__env_substitution_correct():
    conf = Config()
    conf.loads(
        """
_common:
  commands:
    open:
      run: xdg-open .
      env:
        PROJECT: "{{project.name}}"
project:
  path: /path/1
        """
    )

    project = conf.projects["project"]
    command = project.commands["open"]
    clone = command.clone_to(project)
    assert "PROJECT" in clone.env
    assert clone.env["PROJECT"] == "{{project.name}}"
    assert list(clone()) == ["cd /path/1", "export PROJECT=project", "xdg-open ."]


def test_variable__variable_found():
    matches = var_pattern.findall(r"{{project.name}}")
    assert matches == ["name"]


def test_variables_with_text__variables_found():
    matches = var_pattern.findall(r"one {{project.name}} two {{project.path}} three")
    assert matches == ["name", "path"]


def test_variables_in_project__variables_replaced():
    conf = Config()
    conf.loads(
        """
_common:
  env:
    key1: value1_{{project.name}}
project:
  env:
    key2: value2_{{project.name}}
        """
    )

    assert conf.projects["project"].env == {
        "key1": "value1_{{project.name}}",
        "key2": "value2_{{project.name}}",
    }

    assert list(conf.projects["project"]()) == [
        "export key1=value1_project",
        "export key2=value2_project",
    ]
