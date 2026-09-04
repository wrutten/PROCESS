#!/usr/bin/env bash
# Retire a task worktree: relocate its run artifacts into the main tree, THEN
# remove the worktree and delete the branch.
#
# Why this exists.  `git worktree remove --force` deletes untracked files with
# the worktree, and run artifacts under arch_surgery/idf_probe/runs/ are
# untracked by design (CLAUDE.md).  On 2026-09-02 the orchestrator removed
# A26's worktree without relocating first and destroyed the matched-accuracy
# evidence behind a headline correction -- reproducible from merged code, but
# no longer readable.  An earlier cleanup had done it correctly by hand; this
# script exists so it does not depend on remembering.
#
# Usage:  arch_surgery/bin/retire_task_worktree.sh A26-method-fixes
set -euo pipefail

BRANCH=${1:?usage: $0 <branch-name>}
REPO=$(git rev-parse --show-toplevel); cd "$REPO"
SRC="/home/wrutten/projects/PROCESS_surgery_worktrees/${BRANCH}"
DEST_RUNS="${REPO}/arch_surgery/idf_probe/runs"

[ -d "$SRC" ] || { echo "no worktree at ${SRC}" >&2; exit 1; }

git merge-base --is-ancestor "$BRANCH" HEAD 2>/dev/null || {
  echo "REFUSING: ${BRANCH} is not merged into $(git rev-parse --abbrev-ref HEAD)." >&2
  echo "Merge it first, or delete it deliberately with git worktree remove." >&2; exit 1; }

moved=0
# EVERY untracked runs/ directory anywhere under arch_surgery/, not just the
# probe's.  I-16 (2026-09-04): this loop used to scan only
# arch_surgery/idf_probe/runs*/, so when A41 put its gate records under
# arch_surgery/MDA_partitioning_experiment_v3/runs/ the forced removal below
# destroyed them -- the same loss I-14/I-15 record, recurring through a
# coverage gap in the very script written to prevent it.  A run directory is
# defined by its NAME, wherever it sits.
while IFS= read -r d; do
  [ -d "$d" ] || continue
  for e in "$d"*; do
    [ -e "$e" ] || continue
    name=$(basename "$e")
    # namespace anything not already task-scoped, so it cannot collide
    case "$name" in a[0-9]*|A[0-9]*) target="$DEST_RUNS/$name" ;;
                    *) target="$DEST_RUNS/${BRANCH%%-*}_$name" ;; esac
    # NEVER skip on collision -- a skipped entry is destroyed by the forced
    # worktree removal below.  I-15: this script's original skip-and-continue
    # destroyed A29's entire replication tree (375 clean-commit run records)
    # because its runs/a28 collided with the main tree's.  On collision,
    # namespace with the task branch; if even that exists, add a timestamp.
    if [ -e "$target" ]; then target="$DEST_RUNS/${BRANCH}_$name"; fi
    if [ -e "$target" ]; then target="${target}_$(date +%Y%m%dT%H%M%S)"; fi
    # symlinks into the main tree are the one thing genuinely skipped: moving
    # them would shadow the shared recording they point at.
    if [ -L "$e" ]; then echo "  skip (symlink): $name" >&2; continue; fi
    mkdir -p "$DEST_RUNS"; mv "$e" "$target" && moved=$((moved+1))
    echo "  moved: ${d#"$SRC"/}${name} -> ${target#"$DEST_RUNS"/}" >&2
  done
done < <(find "$SRC/arch_surgery" -type d -name 'runs' -o -type d -name 'runs_*' \
         | sort)
echo "relocated ${moved} artifact entries into ${DEST_RUNS}" >&2

# Last line of defence: refuse to destroy anything still unrelocated.  The
# forced removal below deletes untracked files, so a run artifact the loop
# did not see is gone for good (I-14, I-15, I-16).
leftover=$(find "$SRC/arch_surgery" -type d \( -name 'runs' -o -name 'runs_*' \) \
           -exec sh -c '[ -n "$(ls -A "$1" 2>/dev/null)" ] && echo "$1"' _ {} \; )
if [ -n "$leftover" ]; then
  echo "REFUSING to remove ${SRC}: these run directories are still populated:" >&2
  echo "$leftover" >&2
  echo "Relocate them by hand, then re-run.  Nothing has been deleted." >&2
  exit 1
fi

git worktree remove --force "$SRC"
git worktree prune 2>/dev/null || true
git branch -d "$BRANCH" 2>&1 | grep -v "could not lock\|Update of config" || true
echo "retired ${BRANCH}" >&2
