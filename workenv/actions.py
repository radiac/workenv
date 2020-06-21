"""
Command line actions to manage workenv
"""
import os
import subprocess
from pathlib import Path

from . import bash
from .config import Command, Project
from .constants import COMMAND_NAME
from .io import echo, error


registry = {}


def action(fn):
    def wrap(config, actions, args):
        return fn(config, actions, args)

    registry[fn.__name__] = fn
    return wrap


@action
def install(config, actions, args):
    """
    Install workenv into your bashrc
    """
    command_name = COMMAND_NAME
    if len(args) == 1:
        command_name = args[0]
    elif len(args) > 1:
        error("Usage: workenv --install [<as>]")
        return
    bash.install(command_name)
    echo(f"Installed as {command_name}, open a new shell to use")


@action
def edit(config, actions, args):
    """
    Open the yaml source in the shell editor
    """
    if len(args) > 0:
        error("Usage: workenv --edit")
    editor = os.environ.get("EDITOR") or "vim"
    subprocess.call([editor, config.file])


@action
def add(config, actions, args):
    """
    Register a new project or command using the current path
    """
    cwd = Path.cwd()
    project_name, command_name = (args + [None])[0:2]

    # Get or create project
    if not command_name and project_name in config.projects:
        error(f"Project {project_name} already exists")
        return

    if project_name not in config.projects:
        config.projects[project_name] = Project(
            name=project_name, path=cwd, source=[], env=[], run=[], parent=None,
        )
    project = config.projects[project_name]

    if not command_name:
        config.save()
        echo(f"Added project {project_name}")
        return

    if command_name in project.commands:
        error(f"Command {command_name} already exists in project {project_name}")
        return

    project.commands[command_name] = Command(
        name=command_name, path=cwd, source=[], env=[], run=[], parent=project,
    )

    config.save()
    echo(f"Added command {command_name} to project {project_name}")
