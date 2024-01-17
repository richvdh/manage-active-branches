# manage-active-branches

A tool to help keep track of in-flight feature branches in `git`.

## What is it for?

Good open-source etiquette is to break down your contributions to a project
into separate functional blocks; this helps other people in the project
understand your changes and generally helps with project management. In Github,
this generally means having separate git branches and pull requests for each
functional changes.

However, this can lead to a situation where you have several branches in flight
at once, and it becomes hard to keep track of them; it is also fiddly to keep
updating your working branch to include all your in-flight features. That's
where this script comes in.

## Installation

Installation is currently a bit clunky. I use
[Poetry](https://python-poetry.org/docs/). This will install the script into a
virtualenv in `$HOME/.cache/pypoetry/`:

```sh
git clone https://github.com/richvdh/manage-active-branches.git
cd manage-active-branches
poetry install
```

You can then link the script to somewhere on your `$PATH` with something like:

```sh
ln -s $(poetry env info -p)/bin/manage_active_branches ~/.local/bin
```

## Usage

1. Add a branch to the list of "active branches":

   ```sh
   manage_active_branches add my_first_feature
   ```

   (or omit `my_first_feature` to add the current branch).

2. List the currently-active branches:

   ```sh
   manage_active_branches ls  # or omit "ls": it's the default
   ```

   This produces output like:

   ```
   $ manage_active_branches
   my_first_feature
   my_second_feature
   ```

3. Create a "combined" branch:

   ```sh
   manage_active_branches update
   ```

   This command will refuse to run if you have any uncommitted changes in your
   working copy.

   It will create a branch called `active_branches_base` which merges together
   all of your active branches. (If there are merge conflicts, resolve them,
   commit the resolution, and then `manage_active_branches update --continue`.)

4. Remove an active branch:

   ```
   manage_active_branches rm my_first_feature
   ```

## Tips

 * Check out [`git
   rerere`](https://git-scm.com/book/en/v2/Git-Tools-Rerere). It is invaluable
   for keeping track of merge conflict resolutions and repeating them next time
   the same conflict happens.

 * Use a "working" branch for things that you are working on but haven't yet
   knocked into shape for an upstream contribution. (Mine is literally called
   `work`.) Once `manage_active_branches update` updates
   `active_branches_base`, rebase your work branch on top of it.

 * It's often useful to add the default upstream branch (`origin/main`,
   usually) to the list of active branches, so that your work branch includes
   the latest upstream changes.
