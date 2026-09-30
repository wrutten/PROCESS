"""Single evaluations of the V5 copy under a chosen loop, through the V5 harness's pool.

Task A104 (st-stall-mechanism).  Shared by ``loop_sweeps_against_reference.py``
(measurement M0) and ``evaluation_error_at_optimum.py`` (M2).  Nothing here edits
the harness or the driver: a run is one ``pool.Job`` of phase A (the harness's
warmed evaluation child, ``harness/child/evaluate.py``) made by ``pool.run_all``
under a ``Campaign`` whose test set and tolerance are the loop's, whose runs
directory is this task's own root, and whose pool width is two.

A **loop** is ``(arm, test_set, tau)``: the arm composes the arrangement (``AR``
PROCESS's own loop; ``A0`` the flat loop; ``A1`` the flat loop with a constant
owning the burn time, pulsed configurations only; ``A2`` the partitioned loop),
the test set and tolerance are the campaign-level settings every block loop stops
on (driver change DR11).  ``AR`` ignores both; it is run under one of them only
because every job carries them in its identity.

Run kind ``smoke`` (never ``campaign``).  The flat and partitioned runs carry the
driver's observation-only block trace (``PROCESS_ARCH_BLOCK_TRACE``, a job
``override_env``; a different job identity from any campaign run), which gives
each block's scaled residual after every sweep -- how the loop ended.

Reading a record goes through ``harness.core.records.read`` (trap T16).
"""

from __future__ import annotations

import dataclasses
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
V5 = HERE.parent / "MDA_partitioning_experiment_v5"
if str(V5) not in sys.path:
    sys.path.insert(0, str(V5))

from harness.core import config as config_mod  # noqa: E402
from harness.core import pool as pool_mod  # noqa: E402
from harness.core import records as records_mod  # noqa: E402

#: The pool width: the brief's ceiling (7 GB of RAM, the user working).
WORKERS = 2
#: Every run this task makes is under here (moved at hand-back).
ROOT = V5 / "runs" / "st_stall_mechanism"
#: The campaign's own records, read only.
CAMPAIGN_RUNS = V5 / "runs" / "campaign"

CONFIGURATIONS = ("large_tokamak_nof", "low_aspect_ratio_DEMO", "st_regression")
SHORT = {"large_tokamak_nof": "tok", "low_aspect_ratio_DEMO": "lad", "st_regression": "st"}
#: The optimiser's stopping tolerance, from the committed input files
#: (``epsvmc`` lines; asserted against the file by :func:`epsvmc_of`).
EPSVMC = {"large_tokamak_nof": 1e-7, "low_aspect_ratio_DEMO": 1e-8, "st_regression": 1e-9}
#: The driver's block-loop sweep cap (``module_solve.INNER_CAP`` of the copy) and
#: upstream's own pass cap (``Caller.call_models``'s ``range(10)``).
INNER_CAP = 20
UPSTREAM_CAP = 10


@dataclasses.dataclass(frozen=True)
class Loop:
    arm: str
    test_set: str
    tau: float

    @property
    def label(self) -> str:
        if self.arm == "AR":
            return "AR"
        return f"{self.arm} {self.test_set} {self.tau:.0e}"

    @property
    def slug(self) -> str:
        if self.arm == "AR":
            return "AR"
        return f"{self.arm}_{self.test_set}_tau{self.tau:.0e}"


REFERENCE = Loop("AR", "census", 1e-8)


def epsvmc_of(config_name: str) -> float:
    """``epsvmc`` read from the committed input file, asserted against :data:`EPSVMC`."""
    text = (V5 / "harness" / "data" / f"{config_name}.IN.DAT").read_text()
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("epsvmc") and "=" in s:
            value = float(s.split("=", 1)[1].split()[0])
            if value != EPSVMC[config_name]:
                raise SystemExit(f"{config_name}: epsvmc {value} in the input file, {EPSVMC[config_name]} declared")
            return value
    raise SystemExit(f"{config_name}: no epsvmc line in the committed input file")


def campaign_for(loop: Loop, root: Path):
    base = config_mod.default_campaign(test_set=loop.test_set, tau=loop.tau)
    return dataclasses.replace(base, runs_dir=Path(root), workers=WORKERS)


def config_of(campaign, name: str, input_path: Path | None = None):
    config = campaign.configuration(name)
    if input_path is not None:
        config = dataclasses.replace(config, input_path=Path(input_path))
    return config


def evaluation_job(
    campaign,
    config,
    loop: Loop,
    outdir: Path,
    *,
    seed: int = 0,
    regime: str = "unperturbed",
    delta: float | None = None,
    entry_state: Path | None = None,
    stencil_column: int | None = None,
    stencil_sign: int = 1,
    pin_hex: str | None = None,
) -> pool_mod.Job:
    override = {}
    if loop.arm != "AR":
        override["PROCESS_ARCH_BLOCK_TRACE"] = str(Path(outdir) / "block_trace.jsonl")
    return pool_mod.Job(
        phase="A",
        arm=loop.arm,
        config=config,
        seed=seed,
        outdir=Path(outdir),
        regime=regime,
        delta=delta,
        pin_hex=pin_hex,
        entry_state=None if entry_state is None else Path(entry_state),
        stencil_column=stencil_column,
        stencil_sign=stencil_sign,
        run_kind="smoke",
        override_env=override,
    )


def press(groups: dict[Loop, list[pool_mod.Job]], root: Path) -> list[dict]:
    """Run every job, one loop's campaign at a time, two workers, resuming kept records."""
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    outcomes = []
    for loop, jobs in groups.items():
        if not jobs:
            continue
        campaign = campaign_for(loop, root)
        print(f"== {loop.label}: {len(jobs)} job(s)", flush=True)
        outcomes += pool_mod.run_all(jobs, campaign, resume=True)
    return outcomes


# --------------------------------------------------------------------------
# reading
# --------------------------------------------------------------------------


def _trace_lines(outdir: Path) -> list[dict]:
    path = Path(outdir) / "block_trace.jsonl"
    if not path.exists():
        return []
    lines = [json.loads(s) for s in path.read_text().splitlines() if s.strip()]
    return [ln for ln in lines if ln.get("kind") != "header"]


def read_evaluation(outdir: Path, loop: Loop) -> dict[str, Any]:
    """What one evaluation record says: cost, how each loop ended, the values.

    For a run whose warm-up raised (a block at the sweep cap) the measured
    evaluation is not attempted by the child (``evaluate._WarmedEvaluation``), so
    the counts are the warm-up's, which is the same evaluation of the same entry.
    """
    rec = records_mod.read(outdir)
    out: dict[str, Any] = {
        "dir": str(outdir),
        "status": rec.get("status"),
        "failure_class": rec.get("failure_class"),
        "arm": rec.get("campaign_arm"),
        "tau": rec.get("campaign_tau"),
        "test_set": rec.get("campaign_test_set"),
        "tree_git_head": rec.get("tree_git_head"),
        "tree_git_dirty": rec.get("tree_git_dirty"),
        "epsfcn": rec.get("epsfcn"),
        "x_fd": rec.get("x_fd"),
        "input_file": rec.get("campaign_input_file"),
    }
    if out["status"] == "no_record":
        return out
    if out["arm"] != loop.arm:
        raise SystemExit(f"{outdir}: record arm {out['arm']!r}, expected {loop.arm!r}")
    warm = rec.get("evaluation_warmup") or {}
    measured = warm.get("measured")
    source = measured if measured else (warm.get("warmup") or {})
    out["counts_from"] = "measured" if measured else "warm-up (the measured evaluation was not attempted)"
    out["node_calls"] = source.get("node_calls")
    out["sweeps"] = source.get("sweeps")
    if loop.arm == "AR":
        out["ended"] = (
            "agreement" if out["status"] == "ok" else f"raised ({out['failure_class']})"
        )
        out["per_block"] = {"AR": out["sweeps"]}
    else:
        lines = _trace_lines(outdir)
        line = lines[-1] if lines else None
        out["n_trace_lines"] = len(lines)
        blocks: dict[str, Any] = {}
        ended: dict[str, str] = {}
        last_res: dict[str, float | None] = {}
        if line is not None:
            for label, n in (line.get("sweeps") or {}).items():
                blocks[label] = n
                per = (line.get("per_sweep") or {}).get(label)
                if not per:
                    ended[label] = "not iterated" if n <= 1 else "no trace"
                    last_res[label] = None
                    continue
                maxes = [max(s["max"].values()) if s["max"] else 0.0 for s in per]
                last = maxes[-1]
                last_res[label] = last
                if last == 0.0:
                    ended[label] = "bit-identical"
                elif last < loop.tau:
                    ended[label] = "tau"
                else:
                    ended[label] = f"cap ({len(per)} sweeps)"
            out["trace_converged"] = line.get("converged")
            out["residual_per_sweep"] = {
                label: [max(s["max"].values()) if s["max"] else 0.0 for s in per]
                for label, per in (line.get("per_sweep") or {}).items()
            }
        out["per_block"] = blocks
        out["ended_per_block"] = ended
        out["last_residual_per_block"] = last_res
        if out["status"] != "ok":
            out["ended"] = f"raised ({out['failure_class']})"
        elif ended and all(v == "bit-identical" for v in ended.values() if v != "not iterated"):
            out["ended"] = "bit-identical"
        else:
            out["ended"] = "tau"
    audit = rec.get("exit_audit") or {}
    out["audit_residual_max"] = audit.get("residual_max")
    exact = rec.get("exact") or {}
    if exact.get("objf"):
        out["objf"] = float.fromhex(exact["objf"])
        out["conf"] = [float.fromhex(h) for h in exact.get("conf") or []]
    else:
        out["objf"] = None
        out["conf"] = None
    out["t_plant_pulse_burn_hex"] = rec.get("t_plant_pulse_burn_hex")
    return out


def finite(values):
    return [v for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]


def mean(values):
    v = finite(values)
    return sum(v) / len(v) if v else None
