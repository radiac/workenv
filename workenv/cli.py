"""
Command line definition
"""

import os
import sys
from pathlib import Path

from .actions import registry as action_registry
from .bash import autocomplete
from .config import Config, ConfigError
from .constants import COMMAND_VAR, CONFIG_DEFAULT_FILENAME, CONFIG_ENV_VAR
from .io import echo, error


def get_config_path() -> Path:
    path_str = os.environ.get(CONFIG_ENV_VAR, CONFIG_DEFAULT_FILENAME)
    return Path(path_str).expanduser()


def run():
    try:
        config = Config(file=get_config_path())
    except ConfigError as e:
        error(f"Could not load config: {e.message}")
        return

    completions = autocomplete(config)
    if completions is not None:
        for completion in completions:
            echo(completion)
        return

    args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    actions = [action[2:] for action in sys.argv[1:] if action.startswith("--")]

    if len(actions) > 1 or (len(actions) == 0 and len(args) == 0) or len(args) > 2:
        command_name = os.environ.get(COMMAND_VAR, "we")
        error(f"Usage: {command_name} <project> [<command>]")
        error(f"Usage: {command_name} <action> [<project> [<command>]]")
        return

    if actions:
        action = actions[0].lower()
        if action in action_registry:
            action_registry[action](config, actions, args)
            return
        else:
            error(f"Unknown action {action}")
        return

    project_name = args[0]
    if project_name not in config.projects:
        error(f"Unknown project {project_name}")
        return
    project = config.projects[project_name]

    if len(args) == 2:
        command_name = args[1]
        if command_name not in project.commands:
            error(f"Unknown command {command_name} for {project_name}")
            return
        command = project.commands[command_name]

        # If command is common, we need to change its context
        if command.parent != project:
            command = command.clone_to(project)

        shell_cmds = command()
    else:
        shell_cmds = project()

    for shell_cmd in shell_cmds:
        echo(shell_cmd)
