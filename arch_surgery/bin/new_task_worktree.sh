#!/usr/bin/env bash
# Create an isolated worktree for a task branch, at the right commit.
#
# Why this exists (issue I-11).  The agent harness seeds a worktree from the
# repository's *default branch*, not from the current checkout -- 7 of 7
# worktrees this project created landed on `main` (6df46205).  `main` is
# upstream PROCESS: it carries no CLAUDE.md, no arch_surgery/ and no
# TRAPS.md, so an agent starting there has none of this project's rules
# loaded.  The guard cannot live in the tree it guards, so the orchestrator
# creates the worktree itself and hands the agent a path that is already
# correct, instead of asking the agent to detect and repair its own base.
#
# Usage:  arch_surgery/bin/new_task_worktree.sh A24 pulse-residual [start-point]
#
# Prints the worktree path on the last line; everything else is assertions.
set -euo pipefail

BASE_COMMIT=c0ae5b28                 # the frozen experiment base (D2)
TRUNK=architecture_surgery
WORKTREE_ROOT=/home/wrutten/projects/PROCESS_surgery_worktrees

[ $# -ge 2 ] || { echo "usage: $0 <task-label> <keyword> [start-point]" >&2; exit 2; }
TASK=$1; KEYWORD=$2; START=${3:-$TRUNK}

REPO=$(git rev-parse --show-toplevel)
cd "$REPO"

BRANCH="${TASK}-${KEYWORD}"
DEST="${WORKTREE_ROOT}/${BRANCH}"

git show-ref --verify --quiet "refs/heads/${BRANCH}" && {
  echo "REFUSING: branch ${BRANCH} already exists (was it abandoned? rename it)" >&2; exit 1; }
[ -e "$DEST" ] && { echo "REFUSING: ${DEST} already exists" >&2; exit 1; }

START_SHA=$(git rev-parse --verify "${START}^{commit}")
git merge-base --is-ancestor "$BASE_COMMIT" "$START_SHA" || {
  echo "REFUSING: ${START} (${START_SHA}) does not descend from the frozen base ${BASE_COMMIT}" >&2; exit 1; }

mkdir -p "$WORKTREE_ROOT"
git worktree add -b "$BRANCH" "$DEST" "$START_SHA" >&2

# -- assertions on the tree the agent will actually get ------------------
# Descent from the base commit is NOT sufficient on its own: upstream main
# descends from it too, which is exactly why I-11 went unnoticed four times.
# The load-bearing checks are the named tip and the presence of the tree.
fail=0
check() { if eval "$2"; then echo "  ok    $1" >&2; else echo "  FAIL  $1" >&2; fail=1; fi; }
echo "assertions for ${BRANCH}:" >&2
check "branch point is exactly ${START} (${START_SHA:0:8})" \
      "[ \"\$(git -C '$DEST' rev-parse HEAD)\" = '$START_SHA' ]"
check "descends from frozen base ${BASE_COMMIT}" \
      "git -C '$DEST' merge-base --is-ancestor $BASE_COMMIT HEAD"
check "is NOT upstream main" \
      "[ \"\$(git -C '$DEST' rev-parse HEAD)\" != \"\$(git rev-parse main)\" ]"
check "arch_surgery/ present" "[ -d '$DEST/arch_surgery' ]"
check "CLAUDE.md present"    "[ -f '$DEST/CLAUDE.md' ]"
check "TRAPS.md present"     "[ -f '$DEST/arch_surgery/docs/TRAPS.md' ]"
if [ "$fail" != 0 ]; then
  # Tear down rather than leave a half-made worktree: a tree that exists but
  # is wrong is the state this script exists to prevent, and leaving one
  # behind would hand the next caller a "branch already exists" refusal.
  echo "FAILED its assertions -- tearing down, nothing to dispatch" >&2
  git worktree remove --force "$DEST" >&2 2>/dev/null || rm -rf "$DEST"
  git worktree prune >&2 2>/dev/null || true
  git branch -D "$BRANCH" >/dev/null 2>&1 || true
  exit 1
fi

echo "$DEST"
