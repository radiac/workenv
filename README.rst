=======
workenv
=======

A bash shortcut for jumping between local work environments and carrying out tasks
within them.

Requires Python 3.7+ and bash.


Quick example
=============

Example ``~/.workenv_config.yml``::

    myproject:
      path: /path/to/myproject
      source: venv/bin/activate
      run:
      - nvm use
      commands:
        database:
          run: docker-compose up database

Example usage::

    # Jump to /path/to/myproject with the local python virtual environment and nvm
    we myproject

    # Jump to /path/to/myproject and run the database container
    we myproject database

    # Bash completion support
    we m<tab> d<tab>

There is also support for a ``_common`` project with values applied to all projects -
see docs below.


Installation
============

Install to a virtual environment with::

  cd path/to/installation
  virtualenv --python=python3.8 venv
  . venv/bin/activate
  pip install workenv
  workenv --install

This will add the command as ``we`` by adding a line to your ``.bashrc``.

If you would prefer a different command name, you can specify it when installing::

  workenv --install workon

Restart your shell session for your change to take effect.

To uninstall, remove the line from ``.bashrc`` and delete your virtual environment.


Configuration
=============

Add the current path as a new project::

    we --add projectname

Add the current path as a new command::

    we --add projectname command

Open your ``.workenv_config.yml`` for customisation::

    we --edit


Configuration file format
-------------------------

The top level of the YAML file are the names of the projects.

The ``_config`` project controls settings:

``verbose``
  If ``true``, show bash commands when running them

``history``
  If ``true``, add the commands to history

The ``_common`` project defines sources, environment variables and commands which will
be added to all other projects.

A project can have the following attributes:

``path``
  The path to set as the current working directory

``source``
  Path or paths to call using ``source``

``env``
  Dict of environment variables to set

``run``
  Command or list of commands to run

``commands``
  Dict of Command objects

A command can have the same attributes, except it cannot define its own ``commands``.

Values can substitute the project name with ``{{project.name}}``.


Full example
============

Sample ``.workenv_config.yml``::

    _config:
      verbose: true
      history: false
    _common:
      env:
        COMPOSE_PROJECT_NAME: '{{project.name}}'
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
          run: docker-compose up database
    other:
      path: /path/to/other


``we myproject`` is equivalent to typing::

    cd /path/to/myproject
    source venv/bin/activate
    source .env
    export COMPOSE_PROJECT_NAME=myproject
    ./manage.py migrate
    ./manage.py runserver 0:8000

``we myproject database`` is equivalent to typing::

    cd /path/to/myproject
    source venv/bin/activate
    source .env
    export COMPOSE_PROJECT_NAME=myproject
    docker-compose up database

``we other`` is equivalent to typing::

    cd /path/to/other
    export COMPOSE_PROJECT_NAME=other
