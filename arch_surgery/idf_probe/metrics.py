"""MFILE -> metrics dict, and probe-summary rollups.

Rewritten for base commit ``c0ae5b28``.  The variable renaming in that commit
("Rename optimisation problem setup variables", #4481) invalidated the key
names the previous study's version of this file used: ``nvar``, ``neqns``,
``nineqns``, ``ncalls`` and ``nviter`` no longer exist.  The MFILE keys that do
exist in this tree are listed in :data:`SCALAR_KEYS`.
"""

from __future__ import annotations

import json
from pathlib import Path

#: MFILE scalar keys this tree actually writes (verified against a
#: large_tokamak_nof MFILE produced at c0ae5b28).
SCALAR_KEYS = (
    "ifail",
    "norm_objf",
    "sqsumsq",
    "n_iteration_variables",
    "n_solver_iterations",
    "process_runtime",
)

#: Keys whose value legitimately varies between otherwise identical runs.
NONDETERMINISTIC_KEYS = ("process_runtime",)


def parse_mfile(path: Path | str) -> dict:
    """Extract the Stage-0 metrics from an MFILE.

    Returns both parsed floats and, for the quantities the gates compare, the
    *raw* ASCII field, so that a comparison never passes or fails because of
    float re-parsing.
    """
    from process.core.io.mfile import MFile

    mf = MFile(str(path))

    def g(key):
        try:
            return mf.data[key].get_scan(-1)
        except Exception:
            return None

    out: dict = {k: g(k) for k in SCALAR_KEYS}

    itvars: dict[str, float] = {}
    names: dict[str, str] = {}
    for i in range(1, 200):
        key = f"itvar{i:03d}"
        if key not in mf.data:
            break
        itvars[key] = mf.data[key].get_scan(-1)
        names[key] = getattr(mf.data[key], "var_description", "")
    out["itvars"] = itvars
    out["itvar_names"] = names

    # Raw ASCII fields for the gate comparisons.
    out["raw"] = _raw_fields(path, ("norm_objf", "sqsumsq", "ifail", *itvars))
    return out


def _raw_fields(path: Path | str, keys) -> dict[str, str]:
    """Pull the raw value field for ``(key)``-tagged MFILE lines."""
    wanted = {f"({k})": k for k in keys}
    found: dict[str, str] = {}
    for line in Path(path).read_text(errors="replace").splitlines():
        for tag, key in wanted.items():
            if tag + "_" in line or line.rstrip().endswith(tag):
                idx = line.find(tag)
                if idx == -1:
                    continue
                rest = line[idx + len(tag) :].lstrip("_").strip()
                # Trailing " OP" marks an output-only variable; not part of
                # the value.
                if rest.endswith(" OP"):
                    rest = rest[:-3].strip()
                found[key] = rest
    return found


def rel_delta(a, b) -> float:
    """Relative delta of ``b`` w.r.t. ``a``, robust to zeros."""
    if a is None or b is None:
        return float("nan")
    denom = abs(a) if abs(a) > 1e-30 else 1.0
    return abs(b - a) / denom


def load_metrics(path: Path | str) -> dict | None:
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else None


def exact_signature(metrics: dict) -> dict:
    """The tuple of values the bit-identity gates compare.

    Everything here is a hex float literal, i.e. an exact representation of
    the IEEE-754 double.  Two runs match iff these dicts are ``==``.
    """
    exact = metrics.get("exact") or {}
    raw = dict((metrics.get("mfile") or {}).get("raw") or {})
    # process_runtime is excluded by construction: parse_mfile does not put it
    # in `raw`.  Everything else in the MFILE that the gates care about is a
    # 17-significant-digit ASCII field, which round-trips a double exactly.
    return {
        "norm_objf": exact.get("norm_objf"),
        "xcs": exact.get("xcs"),
        "conf_l2": exact.get("conf_l2"),
        "sqsumsq": exact.get("sqsumsq"),
        # The in-memory `norm_objf` is None for an fsolve (evaluation) run --
        # that solver has no objective -- so the MFILE fields carry the
        # comparison for those scenarios.
        "mfile_raw": raw,
    }


def sweep_table(metrics: dict) -> dict:
    """Flatten a run's probe summary into a sweep-anatomy row."""
    probe = metrics.get("probe") or {}
    if not probe.get("enabled"):
        return {"probe": "disabled"}
    allp = probe["all_phases"]
    return {
        "nvar": metrics.get("nvar"),
        "n_constraints": metrics.get("n_constraints"),
        "n_solver_iterations": metrics.get("n_solver_iterations"),
        "call_models": probe["call_models_total"],
        "sweeps_total": probe["sweeps_total"],
        "sweeps_in_call_models": probe["sweeps_inside_call_models"],
        "sweeps_in_output": probe["sweeps_in_output_phase"],
        "mean_sweeps_per_call": allp["mean_sweeps_per_call"],
        "max_sweeps": allp["max_sweeps"],
        "frac_at_floor_2": allp["frac_at_floor_2"],
        "hist": allp["hist"],
        "by_phase": {
            p: {
                "n_call_models": b["n_call_models"],
                "mean_sweeps_per_call": b["mean_sweeps_per_call"],
                "frac_at_floor_2": b["frac_at_floor_2"],
                "hist": b["hist"],
            }
            for p, b in probe["by_phase"].items()
        },
        "n_retries": probe["n_retries"],
        "wall_s": metrics.get("wall_s"),
    }
