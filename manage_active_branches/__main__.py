#!/usr/bin/env python

import argparse
import errno
import os
import subprocess
import sys
from typing import TextIO


class Manager:
    def __init__(self):
        self._git_dir = subprocess.run(
            ("git", "rev-parse", "--path-format=absolute", "--git-dir"),
            stdout=subprocess.PIPE,
        ).stdout.strip()

    def _branches_file_name(self) -> bytes:
        return os.path.join(self._git_dir, b"active-branches")

    def _open_or_create_branches_file(self) -> TextIO:
        try:
            return open(self._branches_file_name(), "r")
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
            return open(self._branches_file_name(), "x+")

    def add_branch(self, branch_name: str) -> int:
        with open(self._branches_file_name(), "r+") as f:
            # slurp in the file and check that the branch is not there already
            for line in f:
                line = line.strip()
                if line == branch_name:
                    print(f"Branch {branch_name} already tracked", file=sys.stderr)
                    break
            else:
                f.write(branch_name)
                f.write("\n")

        return 0

    def remove_branch(self, branch_name: str) -> int:
        found = False

        # open the existing file for reading
        old_file = self._branches_file_name()
        with self._open_or_create_branches_file() as old_fh:
            # open a new file for writing
            new_file = old_file + b".new"
            with open(new_file, "w") as new_fh:
                for line in old_fh.readlines():
                    if line.strip() == branch_name:
                        found = True
                    else:
                        new_fh.write(line)

        old_fh.close()
        new_fh.close()

        if found:
            # move the new file into place
            os.replace(new_file, old_file)
        else:
            os.remove(new_file)
            print(f"Branch {branch_name} not previously tracked", file=sys.stderr)
        return 0

    def ls_branches(self) -> int:
        with self._open_or_create_branches_file() as f:
            for line in f:
                print(line, end="")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    add_parser = subparsers.add_parser(
        "add", help="Add new branch to list of tracked branches"
    )
    add_parser.add_argument("branch_name")
    add_parser.set_defaults(func=add_branch)

    remove_parser = subparsers.add_parser(
        "rm", help="Remove branch from list of tracked branches"
    )
    remove_parser.add_argument("branch_name")
    remove_parser.set_defaults(func=remove_branch)

    ls_parser = subparsers.add_parser(
        "ls", help="Show current list of tracked branches"
    )
    ls_parser.set_defaults(func=ls_branches)

    args = parser.parse_args()
    manager = Manager()
    return args.func(manager, args)


def add_branch(manager: Manager, args: argparse.Namespace) -> int:
    manager.add_branch(args.branch_name)


def remove_branch(manager: Manager, args: argparse.Namespace) -> int:
    manager.remove_branch(args.branch_name)


def ls_branches(manager: Manager, _args: argparse.Namespace) -> int:
    manager.ls_branches()


if __name__ == "__main__":
    exit(main())
