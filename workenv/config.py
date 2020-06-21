"""
Config loader
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar

import yaml


CommandType = TypeVar("CommandType", bound="Command")
ProjectType = TypeVar("ProjectType", bound="Project")

var_pattern = re.compile(r"\{\{\s*project\.([a-z]+)\s*\}\}")


class Command:
    config: Config
    name: str
    _path: Optional[Path]
    _source: List[str]
    _env: Dict[str, str]
    _run: List[str]
    parent: Optional[Command]
    _replacements: Optional[Dict[str, str]]

    def __init__(
        self,
        config: Config,
        name: str,
        path: Optional[Path],
        source: List[str],
        env: Dict[str, str],
        run: List[str],
        parent: Optional[Command],
    ):
        self.config = config
        self.name = name
        self._path = path
        self._source = source
        self._env = env
        self._run = run
        self.parent = parent
        self._replacements = None

    @classmethod
    def from_dict(
        cls: Type[CommandType],
        config: Config,
        name: str,
        data: Dict[str, Any],
        parent: Optional[CommandType] = None,
    ) -> CommandType:
        path: Optional[Path] = None
        if "path" in data:
            path = Path(data["path"])

        source: List[str] = []
        if "source" in data:
            if isinstance(data["source"], str):
                source.append(data["source"])
            else:
                source.extend(data["source"])

        env: Dict[str, str] = {}
        if "env" in data:
            env.update(data["env"])

        run: List[str] = []
        if "run" in data:
            if isinstance(data["run"], str):
                run.append(data["run"])
            else:
                run.extend(data["run"])

        command = cls(
            config=config,
            name=name,
            path=path,
            source=source,
            env=env,
            run=run,
            parent=parent,
        )
        return command

    def __call__(self):
        """
        Generate list of commands to run
        """
        if self.path:
            path = self.replace_values(str(self.path))
            yield f"cd {path}"

        for source in self.source:
            source = self.replace_values(source)
            yield f"source {source}"

        for key, val in self.env.items():
            val = self.replace_values(val)
            yield f"export {key}={val}"

        for run in self.run:
            run = self.replace_values(run)
            yield run

    @property
    def replacements(self):
        """
        Get data for variable replacement
        """
        if not self._replacements:
            self._replacements = dict(name=self.get_project_name())
        return self._replacements

    def replace_values(self, value: str):
        """
        Replace template values
        """
        # This currently uses a naive regex which doesn't support escaping
        # If this ever causes problems we can switch it for a proper parser
        value = var_pattern.sub(
            lambda matchobj: self.replacements.get(matchobj.group(1)), value
        )
        return value

    def to_dict(self):
        data = {}
        if self.path:
            data["path"] = str(self._path)

        for attr in ["source", "env", "run"]:
            val = getattr(self, f"_{attr}")
            if len(val) > 0:
                data[attr] = val

        return data

    def get_project_name(self):
        if self.parent:
            return self.parent.name
        return self.name

    def clone_to(self, parent: Command) -> Command:
        clone = self.from_dict(
            config=self.config, name=self.name, data=self.to_dict(), parent=parent
        )
        return clone

    @property
    def path(self):
        if self._path is None and self.parent:
            return self.parent.path
        return self._path

    @property
    def source(self):
        """
        Inherit from parent if source and path not set
        """
        # Look for common
        common = []
        if self.config.common_project:
            common = self.config.common_project.source

        if self.parent and self._path is None and not self._source:
            return common + self.parent.source

        return common + self._source

    @property
    def env(self):
        data = {}
        if self.config.common_project:
            data.update(self.config.common_project.env)

        if self.parent and not self._env:
            data.update(self.parent.env)
        else:
            data.update(self._env)
        return data

    @property
    def run(self):
        common = []
        if self.config.common_project:
            common = self.config.common_project.run

        return common + self._run


class Project(Command):
    _commands: Dict[str, Command]

    @classmethod
    def from_dict(
        cls: Type[ProjectType],
        config: Config,
        name: str,
        data: Dict[str, Any],
        parent: Optional[ProjectType] = None,
    ) -> ProjectType:
        project = super().from_dict(config, name, data, parent)

        if "commands" in data:
            if not isinstance(data["commands"], dict):
                raise ValueError(
                    f"Unexpected commands in {name} - expected dict,"
                    f" but found {type(data['commands']).__name__}"
                )

            cmd_name: str
            cmd_data: Dict[str, Any]
            for cmd_name, cmd_data in data["commands"].items():
                if cmd_data is None:
                    cmd_data = {}

                # Create command
                command = Command.from_dict(
                    config=config, name=cmd_name, data=cmd_data, parent=project
                )
                project.add_command(cmd_name, command)
        return project

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._commands = {}

    @property
    def commands(self) -> Dict[str, Command]:
        cmds: Dict[str, Command] = {}
        if self.config.common_project:
            cmds.update(self.config.common_project.commands)
        cmds.update(self._commands)
        return cmds

    def add_command(self: Project, name: str, command: Command):
        self._commands[name] = command

    def get_command_names(self):
        return list(self.commands.keys())

    def to_dict(self):
        data = super().to_dict()
        if self._commands:
            data["commands"] = {
                command_name: command.to_dict()
                for command_name, command in self._commands.items()
            }
        return data


class Common(Project):
    """
    Common project
    """

    @property
    def path(self):
        """
        Common project cannot have a path
        """
        return None

    @property
    def source(self):
        return self._source

    @property
    def env(self):
        return self._env

    @property
    def run(self):
        return self._run

    @property
    def commands(self) -> Dict[str, Command]:
        return self._commands


class Config:
    file: Optional[Path]
    projects: Dict[str, Project]
    common_project: Optional[Project]

    # Config variables
    verbose = False
    history = False

    def __init__(self, file: Optional[Path] = None):
        self.file = file
        self.projects = {}
        self.common_project = None

        if file and file.is_file():
            self.load()

    def load(self):
        """
        Load from self.file
        """
        if not self.file:
            raise ValueError("Cannot load a config without specifying the file")
        if not self.file.is_file():
            raise ValueError("Config file does not exist")

        raw = self.file.read_text()
        self.loads(raw)

    def loads(self, raw: str):
        """
        Load from a string
        """
        parsed = yaml.safe_load(raw)
        for name, data in parsed.items():
            if data is None:
                data = {}
            if name == "_config":
                self.from_dict(data)
            elif name == "_common":
                if "path" in data:
                    raise ValueError("Common config cannot define a path")
                self.common_project = Common.from_dict(self, name, data)
            else:
                self.projects[name] = Project.from_dict(self, name, data)

    def get_project_names(self):
        return list(self.projects.keys())

    def from_dict(self, data):
        """
        Load config values from _config definition dict
        """
        self.verbose = data.get("verbose", False)
        self.history = data.get("history", False)

    def to_dict(self):
        """
        Always be explicit with config values - don't worry about adding them when
        writing the yaml
        """
        return {
            "verbose": self.verbose,
            "history": self.history,
        }

    def to_yaml(self):
        projects = {
            "_config": self.to_dict(),
        }

        if self.common_project:
            projects["_common"] = self.common_project.to_dict()

        for project in self.projects.values():
            projects[project.name] = project.to_dict()

        raw = yaml.dump(projects, sort_keys=True)
        return raw

    def save(self):
        if self.file is None:
            raise ValueError("Cannot save a config without specifying the file")

        raw = self.to_yaml()

        self.file.write_text(raw)
