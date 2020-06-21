"""
Bash autocompletion

Based on click
"""
import datetime
import os
import re
import shutil
import sys
from pathlib import Path

from .constants import COMMAND_VAR, COMPLETE_VAR, CONFIG_DEFAULT_FILENAME


# The setup script to be added to .bashrc
INSTALLATION_SCRIPT_BASH = """
# workenv autocomplete
eval "$(%(command_var)s=%(command_name)s %(complete_var)s=setup %(script_path)s)"

"""

# The completion script to run from .bashrc
COMPLETION_ECHO = """
            echo "\\$ $CMD"
"""
COMPLETION_HISTORY = """
            history -s $CMD
"""
COMPLETION_SCRIPT_BASH = """
%(command_name)s() {
    local IFS=$'\n'
    if [[ "$@" =~ (^| )--.* ]]; then
        %(script_path)s "$@"
    else
        CMDS=`%(script_path)s "$@"`;
        for CMD in $CMDS; do
            %(script_echo)s
            %(script_history)s
            eval $CMD
        done
    fi
}
%(complete_func)s() {
    local IFS=$'\n'
    COMPREPLY=( $( env COMP_WORDS="${COMP_WORDS[*]}" \\
                   COMP_CWORD=$COMP_CWORD \\
                   %(complete_var)s=complete \\
                   %(script_path)s ) )
    return 0
}
%(complete_func)s_setup() {
    local IFS=$' '
    local COMPLETION_OPTIONS=""
    local BASH_VERSION_ARR=(${BASH_VERSION//./ })
    # Only BASH version 4.4 and later have the nosort option.
    if [ ${BASH_VERSION_ARR[0]} -gt 4 ] || ([ ${BASH_VERSION_ARR[0]} -eq 4 ] \
&& [ ${BASH_VERSION_ARR[1]} -ge 4 ]); then
        COMPLETION_OPTIONS="-o nosort"
    fi
    complete $COMPLETION_OPTIONS -F %(complete_func)s %(command_name)s
}
%(complete_func)s_setup
"""


def get_script_path():
    script_path = Path(sys.argv[0])
    return script_path


def split_arg_string(string):
    """Given an argument string this attempts to split it into small parts."""
    rv = []
    for match in re.finditer(
        r"('([^'\\]*(?:\\.[^'\\]*)*)'|\"([^\"\\]*(?:\\.[^\"\\]*)*)\"|\S+)\s*",
        string,
        re.S,
    ):
        arg = match.group().strip()
        if arg[:1] == arg[-1:] and arg[:1] in "\"'":
            arg = arg[1:-1].encode("ascii", "backslashreplace").decode("unicode-escape")
        try:
            arg = type(string)(arg)
        except UnicodeError:
            pass
        rv.append(arg)
    return rv


def get_completion_script(config, command_name):
    return (
        COMPLETION_SCRIPT_BASH
        % {
            "complete_func": f"_{command_name}_completion",
            "command_name": command_name,
            "script_path": get_script_path(),
            "complete_var": COMPLETE_VAR,
            "script_echo": COMPLETION_ECHO if config.verbose else "",
            "script_history": COMPLETION_HISTORY if config.history else "",
        }
    ).strip() + ";"


def autocomplete(config):
    complete_var = os.environ.get(COMPLETE_VAR)
    if complete_var is None:
        return None

    elif complete_var == "setup":
        command_name = os.environ.get(COMMAND_VAR)
        return [get_completion_script(config, command_name)]

    elif complete_var == "complete":
        return get_completion_words(config)

    else:
        raise ValueError(f"Unexpected value for env var {COMPLETE_VAR}: {complete_var}")


def get_completion_words(config):
    if "COMP_WORDS" not in os.environ or "COMP_CWORD" not in os.environ:
        return None

    cwords = split_arg_string(os.environ["COMP_WORDS"])
    cword = int(os.environ["COMP_CWORD"])
    args = cwords[1:cword]
    try:
        incomplete = cwords[cword]
    except IndexError:
        incomplete = ""

    if len(args) == 0:
        # Completing a project
        completions = config.get_project_names()
    elif len(args) == 1:
        project = config.projects.get(args[0])
        if not project:
            completions = []
        completions = project.get_command_names()
    else:
        return []

    # Filter
    return [
        completion for completion in completions if completion.startswith(incomplete)
    ]


def install(command_name):
    # Find path to script
    script_path = get_script_path()

    # Ensure there's a config file
    config_path = Path(CONFIG_DEFAULT_FILENAME).expanduser()
    config_path.touch()

    # Find and backup the bashrc
    bashrc = Path("~/.bashrc").expanduser()
    timestamp = datetime.datetime.now().strftime("%Y%M%d%H%m%S")
    shutil.copyfile(bashrc, bashrc.parent / f".bashrc.bak.{timestamp}")

    # Add to .bashrc
    with bashrc.open("a") as file:
        file.write(
            INSTALLATION_SCRIPT_BASH
            % {
                "command_var": COMMAND_VAR,
                "complete_var": COMPLETE_VAR,
                "command_name": command_name,
                "script_path": script_path,
            }
        )
