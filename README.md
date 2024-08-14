# workenv

[![PyPI](https://img.shields.io/pypi/v/workenv.svg)](https://pypi.org/project/workenv/)
[![Tests](https://github.com/radiac/workenv/actions/workflows/ci.yml/badge.svg)](https://github.com/radiac/workenv/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/radiac/workenv/graph/badge.svg?token=EWUKFNYIPX)](https://codecov.io/gh/radiac/workenv)

A shortcut for jumping between local work environments in bash, and carrying out tasks
within them.

Requires Python 3.7+ and bash.


## Quick example

Example `~/.workenv_config.yml`:

```yaml
myproject:
  path: /path/to/myproject
  source: venv/bin/activate
  run:
  - nvm use
  commands:
    database:
      run: docker-compose up database
otherproject:
  file: /path/to/otherproject
```

Example usage:

```bash
# Jump to /path/to/myproject with the local python virtual environment and nvm
we myproject

# Jump to /path/to/myproject and run the database container
we myproject database

# Bash completion support
we m<tab> d<tab>
```

There is also support for a `_common` project with values applied to all projects, and
for projects which define their own settings locally in `,workenv.yml` files - see docs
below.


## Installation

**Recommended**: Install using [pipx](https://pypa.github.io/pipx/):

```bash
pipx install workenv
workenv --install
```

**Alternative**: Install to a virtual environment with::

```bash
cd path/to/installation
python -m venv venv
source venv/bin/activate
pip install workenv
workenv --install
```

Both of these options will add the command as `we` by adding a line to your `.bashrc`.

If you would prefer a different command name, you can specify it when installing:

```bash
workenv --install workon
```

Restart your shell session for your change to take effect.

To uninstall, remove the line from `.bashrc`, and either uninstall with pipx or delete
your virtual environment.


## Configuration

Add the current path as a new project:

```bash
we --add projectname
```

Add the current path as a new command::

```bash
we --add projectname command
```

Open your `.workenv_config.yml` for customisation::

```bash
we --edit
```

The top level of the YAML file are the names of the projects.

Values can substitute the project name with `{{project.name}}` or `{{project.slug}}`.


### Special rules

There are two special top-level YAML objects:

#### `_config`

Controls settings:

* `verbose` - if `true`, show bash commands when running them
* `history` - if `true`, add the commands to history

#### `_common`

Common project which can define a common `source`, `env`, `run` and `commands`
which will be added to all other projects, regardless of whether they define their
own.

The common project cannot specify a path.


### Project rules

A project can have the following attributes:

#### `path`

The path to set as the current working directory. This will be the first command run.

Example:

```yaml
myproject:
  path: /path/to/foo
```

Bash equivalent:

```bash
cd /path/to/foo
```

#### `source`

Path or paths to call using `source`

Example:

```yaml
myproject:
  source:
  - venv/bin/activate
  - .env
```

Bash equivalent:

```bash
source venv/bin/activate
source .env
```

#### `env`

Dict of environment variables to set

Example:

```yaml
myproject:
  env:
    COMPOSE_PROJECT_NAME: my_project
```

Bash equivalent:

```bash
export COMPOSE_PROJECT_NAME=my_project
```

#### `run`

Command or list of commands to run

Example:

```yaml
myproject:
  run:
  - nvm use
  - yvm use
```

Bash equivalent::

```bash
nvm use
yvm use
```

#### `commands`

Dict of Command objects

Example:

```yaml
myproject:
  commands:
    database:
      run: docker-compose up database
```

Usage:

```bash
we myproject database
```

Bash equivalent:

```bash
docker-compose up database
```

A command will inherit the `path` and `env` of its parent project, unless it defines its
own.

It will inherit the `source` of its parent project only if it does not specify its own
path or source.

A command can have the same attributes as a project, except it cannot define its own
`commands`.


## Full example

Putting together all the options above into a sample `.workenv_config.yml`:

```yaml
_config:
  verbose: true
  history: false
_common:
  env:
    COMPOSE_PROJECT_NAME: '{{project.slug}}'
    PS1: '"\[\e[01;35m\]{{project.slug}}>\[\e[00m\]$PS1"'
  commands:
    open:
      run: xdg-open .
myproject:
  path: /path/to/myproject
  source:
  - venv/bin/activate
  - .env
  run:
  - ./manage.py migrate
  - ./manage.py runserver 0:8000
  commands:
    database:
      run: docker compose up database
other:
  path: /path/to/other
something-else:
  config: /path/to/somethingelse
```

`we myproject` is equivalent to typing:

```bash
cd /path/to/myproject
source venv/bin/activate
source .env
export COMPOSE_PROJECT_NAME=myproject
./manage.py migrate
./manage.py runserver 0:8000
```

`we myproject database` is equivalent to typing:

```bash
cd /path/to/myproject
source venv/bin/activate
source .env
export COMPOSE_PROJECT_NAME=myproject
docker compose up database
```

`we other` is equivalent to typing:

```bash
cd /path/to/other
export COMPOSE_PROJECT_NAME=other
```

`we other open` is equivalent to:

```bash
cd /path/to/myproject
export COMPOSE_PROJECT_NAME=other
xdg-open .
```

and `something-else` will be configured in `/path/to/somethingelse/.workenv.yml`; `path`
will be automatically set to that dir:

```yaml
source:
- venv/bin/activate
- .env
run:
- ./manage.py migrate
- ./manage.py runserver 0:8000
commands:
  database:
    run: docker compose up database
```
