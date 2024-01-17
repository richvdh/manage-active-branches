#!/usr/bin/env python

import argparse
import errno
import os
import subprocess
import sys
from typing import TextIO, Iterable, List

ACTIVE_BRANCH_NAME = "active_branches_base"


class ManagerError(Exception):
    def __init__(self, message: str, code: int):
        super().__init__(message)
        self.code = code


class Manager:
    def __init__(self, verbose: bool):
        self._verbose = verbose
        self._git_dir = self._capture_cmd(
            "git", "rev-parse", "--path-format=absolute", "--git-dir"
        )

    def _capture_cmd(self, *args: str, **kwargs) -> bytes:
        """Run the given command, check its exitcode, and return its stdout"""
        if self._verbose:
            print(f"> {' '.join(args)}", file=sys.stderr)
        return subprocess.run(
            args, check=True, stdout=subprocess.PIPE, **kwargs
        ).stdout.strip()

    def _run_cmd(self, *args: str, **kwargs) -> None:
        """Run the given command and check its exitcode"""
        if self._verbose:
            print(f"> {' '.join(args)}", file=sys.stderr)
        subprocess.run(args, check=True, **kwargs)

    def assert_wc_clean(self):
        """Check that the working copy is clean and throw an error if not"""
        status = self._capture_cmd(
            "git", "status", "--untracked-files=no", "--porcelain"
        )

        # if there is any output, the WC is dirty
        if status != b"":
            raise ManagerError(f"Working copy has uncommitted changes", 1)

    def _branches_file_name(self) -> bytes:
        return os.path.join(self._git_dir, b"active-branches")

    def _open_or_create_branches_file(self) -> TextIO:
        try:
            return open(self._branches_file_name(), "r")
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
            return open(self._branches_file_name(), "x+")

    def _get_active_branches(self) -> Iterable[str]:
        with self._open_or_create_branches_file() as f:
            for line in f:
                yield line.strip()

    def add_branch(self, branch_names: List[str]) -> int:
        if len(branch_names) == 0:
            branch_names = [self._capture_cmd(
                "git", "rev-parse", "--abbrev-ref", "HEAD"
            ).decode()]

        with open(self._branches_file_name(), "r+") as f:
            # slurp in the file and check that the branch is not there already
            for line in f:
                line = line.strip()
                if line in branch_names:
                    print(f"Branch {line} already tracked", file=sys.stderr)
                    break
            else:
                f.writelines(n + "\n" for n in branch_names)

        return 0

    def remove_branch(self, branch_names: List[str]) -> int:
        unfound_branchnames = set(branch_names)

        # open the existing file for reading
        old_file = self._branches_file_name()
        with self._open_or_create_branches_file() as old_fh:
            # open a new file for writing
            new_file = old_file + b".new"
            with open(new_file, "w") as new_fh:
                for line in old_fh.readlines():
                    branch = line.strip()
                    if branch in unfound_branchnames:
                        unfound_branchnames.remove(branch)
                    else:
                        new_fh.write(line)

        old_fh.close()
        new_fh.close()

        unfound = next(iter(unfound_branchnames), None)
        if unfound is None:
            # move the new file into place
            os.replace(new_file, old_file)
        else:
            os.remove(new_file)
            print(f"Branch {unfound} not previously tracked", file=sys.stderr)
        return 0

    def ls_branches(self) -> int:
        for branch in self._get_active_branches():
            print(branch)
        return 0

    def update(self, continue_merge: bool) -> int:
        """Create or update our tracking branch"""
        self.assert_wc_clean()

        active_branches = list(self._get_active_branches())

        if not continue_merge:
            # create the branch based on the common base of the branches for this repo
            merge_base = self._capture_cmd("git", "merge-base", "--octopus", *active_branches).decode()
            self._run_cmd("git", "checkout", "-B", ACTIVE_BRANCH_NAME, merge_base)

        # merge each of the active branches into it in turn.
        for branch_name in active_branches:
            print(f"Merging {branch_name}", file=sys.stderr)
            self._run_cmd("git", "merge", "--no-edit", branch_name)
            print("\n-----\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="display commands before running them",
    )

    subparsers = parser.add_subparsers(metavar="subcommand")

    add_parser = subparsers.add_parser(
        "add", help="Add new branch to list of tracked branches"
    )
    add_parser.add_argument(
        "branch_name",
        nargs="*",
        help="Names of branches to add. Defaults to the current branch.",
    )
    add_parser.set_defaults(func=add_branch)

    remove_parser = subparsers.add_parser(
        "rm", help="Remove branch from list of tracked branches"
    )
    remove_parser.add_argument(
        "branch_name",
        nargs="+",
        help="Names of branches to remove.",
    )
    remove_parser.set_defaults(func=remove_branch)

    ls_parser = subparsers.add_parser(
        "ls", help="Show current list of tracked branches"
    )
    ls_parser.set_defaults(func=ls_branches)

    update_parser = subparsers.add_parser(
        "update", help=f"Create, or update, {ACTIVE_BRANCH_NAME} branch"
    )
    update_parser.add_argument(
        "--continue",
        action="store_true",
        dest="continue_merge",
        help="Continue a previous update (do not reset branch",
    )
    update_parser.set_defaults(func=update)

    args = parser.parse_args()
    manager = Manager(verbose=args.verbose)

    # Default to 'ls' if no subparser specified
    func = getattr(args, 'func', ls_branches)
    try:
        return func(manager, args)
    except ManagerError as e:
        print(e, file=sys.stderr)
        return e.code


def add_branch(manager: Manager, args: argparse.Namespace) -> int:
    manager.add_branch(args.branch_name)


def remove_branch(manager: Manager, args: argparse.Namespace) -> int:
    manager.remove_branch(args.branch_name)


def ls_branches(manager: Manager, _args: argparse.Namespace) -> int:
    manager.ls_branches()


def update(manager: Manager, args: argparse.Namespace) -> int:
    manager.update(continue_merge=args.continue_merge)


if __name__ == "__main__":
    exit(main())
