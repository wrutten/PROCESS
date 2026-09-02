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
for d in "$SRC"/arch_surgery/idf_probe/runs*/ ; do
  [ -d "$d" ] || continue
  for e in "$d"*; do
    [ -e "$e" ] || continue
    name=$(basename "$e")
    # namespace anything not already task-scoped, so it cannot collide
    case "$name" in a[0-9]*|A[0-9]*) target="$DEST_RUNS/$name" ;;
                    *) target="$DEST_RUNS/${BRANCH%%-*}_$name" ;; esac
    if [ -e "$target" ]; then echo "  skip (exists): $name" >&2; continue; fi
    mkdir -p "$DEST_RUNS"; mv "$e" "$target" && moved=$((moved+1))
  done
done
echo "relocated ${moved} artifact entries into ${DEST_RUNS}" >&2

git worktree remove --force "$SRC"
git worktree prune 2>/dev/null || true
git branch -d "$BRANCH" 2>&1 | grep -v "could not lock\|Update of config" || true
echo "retired ${BRANCH}" >&2
