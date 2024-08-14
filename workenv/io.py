"""
Simple io wrappers
"""

import sys


def echo(line):
    sys.stdout.write(line)
    sys.stdout.write("\n")


def error(line):
    sys.stderr.write(line)
    sys.stderr.write("\n")
