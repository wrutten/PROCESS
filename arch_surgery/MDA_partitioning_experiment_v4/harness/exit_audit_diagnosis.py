"""The stage that diagnoses the exit audit's one component above the tolerance.

One entry point, three stages, every number it publishes produced by running
it.  Nothing here is typed at a shell prompt: the census reads committed
artifacts and the experiment's own copy of PROCESS, the runs go through
:mod:`harness.pool` like every other PROCESS run this package starts, and the
report is rendered from what those runs wrote.

    python -m harness.exit_audit_diagnosis census
    python -m harness.exit_audit_diagnosis runs
    python -m harness.exit_audit_diagnosis report
    python -m harness.exit_audit_diagnosis all

The question
------------
With the exit audit taken where the experiment plan declares — at the entry to
the output path, from a bit-exact snapshot of the state the solve handed over —
exactly one restricted coupling-state component sits at or above the tolerance
on both pulsed configurations, in every arm: ``tfcoil.insstrain``, at about
7e-3 scaled.  Its own measured scale is its own magnitude, so that is a change
of about 0.7 % in the value.  The flat control's loop, meanwhile, stops on that
same ruler over that same component set and converges every evaluation.  Both
cannot be true of one map, so one of the two statements is about a different
map, and this stage finds out which.

Heritage: task **A61 (insstrain-diagnosis)**.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import arms as arms_mod
from . import audit_map as audit_map_mod
from . import input_files as input_files_mod
from . import pool as pool_mod
from . import child as child_mod
from . import records as records_mod
from .config import Campaign, default_campaign

#: The component the diagnosis is about.
COMPONENT = "tfcoil.insstrain"

#: Where this stage's runs and its own outputs go, under the campaign's runs
#: directory.  Untracked by design (bulk run artifacts are never committed);
#: the summary this stage writes is what a report quotes.
SUBPATH = "gates/exit_audit_diagnosis"

#: The runs, declared as data.  One row per (configuration, arm, seed).  The
#: reference arm is here because the component is above the tolerance there
#: too — the finding is about PROCESS, not about an architecture switch — and
#: the steady-state configuration is here because it shows **nothing**, which
#: is a result that has to be reachable from the same entry point as the
#: others.
RUNS: tuple[dict[str, Any], ...] = (
    {"configuration": "large_tokamak_nof", "arm": "B0", "seed": 0},
    {"configuration": "large_tokamak_nof", "arm": "BR", "seed": 0},
    {"configuration": "large_tokamak_nof", "arm": "B0", "seed": 1},
    {"configuration": "large_tokamak_nof", "arm": "B1", "seed": 0},
    {"configuration": "low_aspect_ratio_DEMO", "arm": "B0", "seed": 0},
    {"configuration": "low_aspect_ratio_DEMO", "arm": "BR", "seed": 0},
    {"configuration": "st_regression", "arm": "B0", "seed": 0},
)


class DiagnosisError(RuntimeError):
    """A refusal.  Never downgraded into a warning."""


def root(campaign: Campaign) -> Path:
    return Path(campaign.runs_dir) / SUBPATH


def _git_head() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(Path(__file__).resolve().parent),
        ).stdout.strip()
    except Exception:  # noqa: BLE001 - recorded, never raised
        return None


# --------------------------------------------------------------------------
# stage 1 — the census: what the component is, and what computes it
# --------------------------------------------------------------------------

#: The model files the census reads, relative to the copy's package root.  Read
#: rather than described: a report that says "the model does X" without a line
#: number is an assertion.
MODEL_FILES: tuple[str, ...] = (
    "process/models/tfcoil/base.py",
    "process/models/tfcoil/superconducting.py",
    "process/models/tfcoil/resistive.py",
    "process/data_structure/tfcoil_variables.py",
)

#: The settings the census reports from each committed input file, because they
#: are what selects the branch that computes the component.
INPUT_FILE_KEYS: tuple[str, ...] = (
    "i_tf_stress_model",
    "i_tf_sup",
    "i_tf_turn_type",
    "n_rad_per_layer",
)


def census(campaign: Campaign) -> dict[str, Any]:
    """Which node writes the component, from what, and how it is tested.

    Every fact here is read from a committed artifact or from the experiment's
    own copy of PROCESS at the commit this stage runs at; nothing is quoted
    from a document.
    """
    tree = Path(campaign.tree)
    result: dict[str, Any] = {
        "stage": "census",
        "component": COMPONENT,
        "taken": _dt.datetime.now().isoformat(timespec="seconds"),
        "tree": str(tree),
        "tree_git_head": _git_head(),
        "configurations": {},
    }

    census_path = Path(campaign.data_dir) / "node_writesets.json"
    if not census_path.exists():
        raise DiagnosisError(
            f"the committed write census is not at {census_path}; the writer "
            f"of {COMPONENT} is derived from it and is not guessed from a "
            f"name"
        )
    write_census = json.loads(census_path.read_text())

    for config in campaign.configurations:
        row: dict[str, Any] = {"name": config.name, "pulsed": config.pulsed}

        # -- the writer, from the committed run-time write census ---------
        per_configuration = write_census["per_scenario"].get(config.name)
        if per_configuration is None:
            raise DiagnosisError(
                f"the committed write census names no {config.name}; it "
                f"covers {sorted(write_census['per_scenario'])}"
            )
        by_node = per_configuration["writes_by_node"]
        writers = sorted(
            node
            for node, fields in by_node.items()
            if COMPONENT in (fields or [])
        )
        row["n_nodes_in_the_census"] = len(by_node)
        row["writers"] = writers
        row["writer_module"] = {
            node: per_configuration.get("node_module", {}).get(node)
            for node in writers
        }

        # -- its place in the coupling state, from the committed artifact --
        spec_record = json.loads(Path(config.coupling_state_path).read_text())
        entry = next(
            (c for c in spec_record["components"] if c["key"] == COMPONENT), None
        )
        row["coupling_state_artifact"] = str(config.coupling_state_path)
        row["n_components"] = spec_record["n_components"]
        row["in_the_coupling_state"] = entry is not None
        if entry is not None:
            row["category"] = entry.get("category")
            row["kind"] = entry.get("kind")
            row["scale"] = entry.get("scale")
            row["scale_hex"] = entry.get("scale_hex")
            row["scale_from_floor"] = entry.get("scale_from_floor")
            row["n_points_scale_measured_over"] = entry.get(
                "n_points_scale_measured_over"
            )
            row["magnitude_min"] = entry.get("char_mag_min")
            row["magnitude_max"] = entry.get("char_mag_max")
            row["value_if_discrete"] = entry.get("value")
        row["how_the_scale_was_measured"] = spec_record["method"]["scale"]
        row["harvest"] = {
            "path": spec_record["harvest"]["path"],
            "n_design_points": spec_record["harvest"]["n_design_points"],
            "content_sha256": spec_record["harvest"]["content_sha256"],
        }

        # -- the block whose write set the flat loop compares --------------
        write_sets = json.loads(Path(config.write_sets_path).read_text())
        row["blocks_whose_write_set_contains_it"] = sorted(
            label
            for label, members in (write_sets.get("subsets") or {}).items()
            if COMPONENT in (members or [])
        )

        # -- what the input file sets --------------------------------------
        parsed = input_files_mod.parse_input_file(config.input_path)
        settings = parsed["integer_settings"]
        row["input_file"] = str(config.input_path)
        row["input_file_sha256"] = parsed["sha256"]
        row["input_file_settings"] = {
            key: settings.get(key) for key in INPUT_FILE_KEYS
        }
        row["input_file_settings_note"] = (
            "a key absent from the input file takes the data structure's own "
            "default, which the source census below reports with its line"
        )
        # -- what runs between the loop's exit and the output path's entry --
        #
        # The coupling-state predicate is evaluated immediately after a sweep,
        # so the loop's exit state is the state that sweep left.  What happens
        # after it and before the audit's declared position is the objective
        # and constraint layer, which the write census covers as its own node,
        # and — on an arm that defers nodes to once per run — those nodes,
        # which run INSIDE the output path and therefore after the snapshot.
        layer_writes = by_node.get("objective_constraints") or []
        spec_keys = {c["key"] for c in spec_record["components"]}
        row["between_the_loop_exit_and_the_output_path"] = {
            "objective_and_constraint_layer": {
                "census_node": "objective_constraints",
                "n_writes": len(layer_writes),
                "writes": sorted(layer_writes),
                "writes_in_the_coupling_state": sorted(
                    set(layer_writes) & spec_keys
                ),
            },
            "per_run_deferred_nodes": {
                "note": (
                    "they run inside write_output_files, after the snapshot "
                    "the audit is taken from, and only on an arm whose matrix "
                    "cell sets the per-run deferral"
                ),
                "artifact": str(config.per_run_artifact(lifted_input_file=False)),
                "nodes": json.loads(
                    Path(
                        config.per_run_artifact(lifted_input_file=False)
                    ).read_text()
                )["post_solve_nodes"],
            },
        }
        result["configurations"][config.name] = row

    # -- the code, with line numbers ---------------------------------------
    result["source"] = _source_census(tree)
    return result


def _source_census(tree: Path) -> dict[str, Any]:
    """Every line of the copy's model code that mentions the two names.

    The component and the radial-discretisation setting, located rather than
    described.  A line is reported with its file, its number and its text, and
    with the function and class it sits in, so that the ``run``/``output`` split
    (trap T1) is visible rather than asserted.
    """
    import ast

    names = (COMPONENT.split(".", 1)[1], "n_rad_per_layer")
    out: dict[str, Any] = {"names": list(names), "files": {}}
    for relative in MODEL_FILES:
        path = tree / relative
        if not path.exists():
            out["files"][relative] = {"error": f"{path} is not there"}
            continue
        text = path.read_text()
        lines = text.splitlines()
        try:
            tree_ast = ast.parse(text)
            functions = [
                (node.lineno, node.end_lineno, node.name)
                for node in ast.walk(tree_ast)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            classes = [
                (node.lineno, node.end_lineno, node.name)
                for node in ast.walk(tree_ast)
                if isinstance(node, ast.ClassDef)
            ]
            tests = []
            for node in ast.walk(tree_ast):
                if isinstance(node, ast.If):
                    for branch, body in (
                        ("if", node.body),
                        ("else", node.orelse),
                    ):
                        if not body:
                            continue
                        start = body[0].lineno
                        end = max(
                            getattr(item, "end_lineno", item.lineno)
                            for item in body
                        )
                        tests.append(
                            (start, end, branch, ast.unparse(node.test))
                        )
        except SyntaxError:
            functions, classes, tests = [], [], []
        hits = []
        for number, line in enumerate(lines, start=1):
            if not any(name in line for name in names):
                continue
            enclosing = sorted(
                (f for f in functions if f[0] <= number <= (f[1] or f[0])),
                key=lambda f: (f[1] or f[0]) - f[0],
            )
            in_class = [c[2] for c in classes if c[0] <= number <= (c[1] or c[0])]
            guards = sorted(
                (t for t in tests if t[0] <= number <= t[1]),
                key=lambda t: t[1] - t[0],
            )
            hits.append(
                {
                    "line": number,
                    "text": line.strip(),
                    "function": enclosing[0][2] if enclosing else None,
                    "class": in_class[0] if in_class else None,
                    "innermost_guard": (
                        None
                        if not guards
                        else f"{guards[0][2]} {guards[0][3]}"
                    ),
                    "guards": [f"{g[2]} {g[3]}" for g in guards[:4]],
                }
            )
        defaults = {}
        for hit in hits:
            match = re.match(
                r"^(\w+)\s*:\s*\w+\s*=\s*([-\w.]+)\s*$", hit["text"]
            )
            if match and hit["function"] is None:
                defaults[match.group(1)] = match.group(2)
        out["files"][relative] = {
            "n_hits": len(hits),
            "hits": hits,
            "data_structure_defaults": defaults,
        }
    return out


# --------------------------------------------------------------------------
# stage 2 — the runs
# --------------------------------------------------------------------------


def jobs(
    campaign: Campaign, *, only: Sequence[str] | None = None
) -> list[pool_mod.Job]:
    """The declared runs, as jobs.  Every one a gate run, with the trace on.

    ``only`` narrows the set to the named ``configuration/arm/seed`` keys, for
    a smoke run of the instrument itself.  It never adds a run, and the report
    stage uses the same filter, so a summary made under a filter names the
    runs it is missing rather than shrinking its own denominator.
    """
    out: list[pool_mod.Job] = []
    for row in RUNS:
        key = f"{row['configuration']}/{row['arm']}/seed{int(row['seed']):03d}"
        if only and key not in only:
            continue
        config = campaign.configuration(row["configuration"])
        arm = row["arm"]
        if arm not in arms_mod.active_arms(config, "B"):
            continue
        seed = int(row["seed"])
        out.append(
            pool_mod.Job(
                phase="B",
                arm=arm,
                config=config,
                seed=seed,
                outdir=root(campaign)
                / "runs"
                / config.name
                / arm
                / pool_mod.seed_directory(seed),
                regime="unperturbed" if seed == 0 else "perturbed",
                delta=campaign.delta,
                run_kind="gate",
                override_env={audit_map_mod.TRACE_VARIABLE: "1"},
            )
        )
    return out


def make_runs(
    campaign: Campaign,
    *,
    resume: bool = False,
    only: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Start the declared runs.  Nothing is compared here.

    An arm that reads the lifted input file needs it derived first; that is a
    committed stage of this package and it is called here rather than assumed,
    so that "the derived input file is not there" is a refusal at this stage's
    front door rather than a failed run three jobs in.
    """
    planned = jobs(campaign, only=only)
    needs_lifted = {
        job.config.name
        for job in planned
        if arms_mod.ARMS[job.arm].input_file == "lifted" and job.config.pulsed
    }
    derivation: dict[str, Any] = {}
    for name in sorted(needs_lifted):
        config = campaign.configuration(name)
        if not input_files_mod.is_lifted_available(config, campaign):
            code, record = input_files_mod.stage_derive(
                campaign, configurations=[name]
            )
            derivation[name] = {"exit_code": code, "record": record}
            if code != 0:
                raise DiagnosisError(
                    f"{name}: the lifted input file could not be derived "
                    f"(exit code {code}); the arm that reads it is refused "
                    f"rather than run against the committed one under the "
                    f"lifted arm's name"
                )
        derivation.setdefault(name, {})["identity"] = input_files_mod.assert_lifted(
            config, campaign
        )
    results = pool_mod.run_all(planned, campaign, resume=resume)
    manifest = {
        "stage": "runs",
        "captured": _dt.datetime.now().isoformat(timespec="seconds"),
        "tree_git_head": _git_head(),
        "trace_variable": audit_map_mod.TRACE_VARIABLE,
        "n_runs": len(planned),
        "n_runs_declared": len(RUNS),
        "filter": list(only or ()),
        "lifted_input_files": derivation,
        "runs": [
            {
                "configuration": job.config.name,
                "arm": job.arm,
                "seed": job.seed,
                "outdir": str(job.outdir),
                "status": results[i].get("status"),
                "rc": results[i].get("rc"),
            }
            for i, job in enumerate(planned)
        ],
        "declared_but_inactive": [
            dict(row)
            for row in RUNS
            if row["arm"]
            not in arms_mod.active_arms(
                campaign.configuration(row["configuration"]), "B"
            )
        ],
    }
    path = root(campaign) / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    manifest["manifest"] = str(path)
    return manifest


# --------------------------------------------------------------------------
# stage 3 — the report's numbers
# --------------------------------------------------------------------------


def summarise(
    campaign: Campaign, *, only: Sequence[str] | None = None
) -> dict[str, Any]:
    """Read what the runs wrote and put the published quantities in one file.

    A run whose observation is missing is named as missing, never skipped: a
    table over the runs that happened to work is a table over a population
    nobody declared (trap T11).
    """
    summary: dict[str, Any] = {
        "stage": "report",
        "component": COMPONENT,
        "made": _dt.datetime.now().isoformat(timespec="seconds"),
        "tree_git_head": _git_head(),
        "n_runs_declared": len(RUNS),
        "filter": list(only or ()),
        "rows": [],
        "missing": [],
    }
    for job in jobs(campaign, only=only):
        directory = Path(job.outdir)
        key = f"{job.config.name}/{job.arm}/seed{job.seed:03d}"
        record_path = directory / "metrics.json"
        observation_path = directory / audit_map_mod.OBSERVATION_FILE
        if not record_path.exists() or not observation_path.exists():
            summary["missing"].append(
                {
                    "key": key,
                    "record": record_path.exists(),
                    "observation": observation_path.exists(),
                    "outdir": str(directory),
                }
            )
            continue
        record = records_mod.read(directory)
        observation = json.loads(observation_path.read_text())
        summary["rows"].append(
            _row(key, job, record, observation, campaign, directory)
        )
    summary["n_rows"] = len(summary["rows"])
    summary["n_missing"] = len(summary["missing"])
    path = root(campaign) / "summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, default=str) + "\n")
    summary["written_to"] = str(path)
    (root(campaign) / "summary.md").write_text(render(summary))
    return summary


def _row(key, job, record, observation, campaign, directory) -> dict[str, Any]:
    """One run's published quantities, from its record and its observation."""
    audit = record.get("exit_audit") or {}
    restricted = _restricted(audit, job, campaign, directory)
    comparisons = observation.get("state_comparisons", {})
    structures = observation.get("data_structure_comparisons", {})
    sweeps = {s["name"]: s for s in observation.get("sweeps", [])}
    row: dict[str, Any] = {
        "key": key,
        "configuration": job.config.name,
        "arm": job.arm,
        "seed": job.seed,
        "status": record.get("status"),
        "ifail": (record.get("exit_forensics") or {}).get("ifail"),
        "n_solver_iterations": record.get("n_solver_iterations"),
        "audit_position": record.get("audit_position"),
        "audit_position_declared": record.get("audit_position_declared"),
        "record_audit": {
            "residual_max_hex": audit.get("residual_max_hex"),
            "argmax": (audit.get("brief") or {}).get("argmax"),
            "n_above_tau": (audit.get("brief") or {}).get("n_above"),
            "restricted_max_hex": restricted.get("max_hex"),
            "restricted_argmax": restricted.get("argmax"),
            "restricted_n_above_tau": restricted.get("n_above"),
            "n_kept": restricted.get("n_kept"),
            "n_excluded": restricted.get("n_excluded"),
        },
        "node_calls_solve_phase": record.get("node_calls_solve_phase"),
        "output_path": record.get("output_path"),
        "output_loop_sweeps": record.get("output_loop_sweeps"),
        "sweeps_per_eval": record.get("sweeps_per_eval"),
        "candidate_field": audit_map_mod.CANDIDATE_FIELD,
        "candidate_before_after": (
            (
                observation.get("data_structure_comparisons", {})
                .get(
                    "entry_to_write_output_files__vs__before_the_record_audit",
                    {},
                )
                .get("detail")
                or {}
            ).get(audit_map_mod.CANDIDATE_FIELD)
        ),
        "design_vector_identity": {
            "last_evaluation_is_the_audited_point": (
                (observation.get("design_vectors") or {}).get("last_evaluation")
                == (observation.get("design_vectors") or {}).get("audit_x_xcm")
            ),
            "last_sweep_is_the_audited_point": (
                (observation.get("design_vectors") or {}).get("last_sweep")
                == (observation.get("design_vectors") or {}).get("audit_x_xcm")
            ),
            "n_iteration_variables": len(
                (observation.get("design_vectors") or {}).get("audit_x_xcm") or []
            ),
        },
        "restore_diagnostics": _restore_diagnostics(observation),
        "sweeps_seen": observation.get("n_sweeps_seen"),
        "evaluations_seen": observation.get("n_evaluations_seen"),
        "trace_errors": observation.get("errors"),
        "state_comparisons": {
            name: {
                "n_not_bit_identical": value.get("n_not_bit_identical"),
                "not_bit_identical": value.get("not_bit_identical"),
                "max_hex": value.get("max_hex"),
                "argmax": value.get("argmax"),
                "n_above_tau": value.get("n_above_tau"),
                "compared": value.get("compared"),
                "why": value.get("why"),
            }
            for name, value in comparisons.items()
        },
        "data_structure": {
            name: {
                "compared": value.get("compared"),
                "n_compared": value.get("n_compared"),
                "n_differ": value.get("n_differ"),
                "n_outside_the_coupling_state": value.get(
                    "n_outside_the_coupling_state"
                ),
                "outside_the_coupling_state": value.get(
                    "outside_the_coupling_state"
                ),
                "detail": value.get("detail"),
                "why": value.get("why"),
            }
            for name, value in structures.items()
        },
        "fields_put_back_for_the_solve_phase_map": observation.get(
            "fields_put_back_for_the_solve_phase_map"
        ),
        "sweeps": {
            name: {
                "residual_max_hex": (
                    (sweep.get("rulers") or {}).get("frozen") or {}
                ).get("residual_max_hex"),
                "argmax": (
                    (sweep.get("rulers") or {}).get("frozen") or {}
                ).get("argmax"),
                "n_above_tau": (
                    (sweep.get("rulers") or {}).get("frozen") or {}
                ).get("n_above_tau"),
                "mixed_residual_max_hex": (
                    (sweep.get("rulers") or {}).get("mixed") or {}
                ).get("residual_max_hex"),
                "node_calls": sweep.get("node_calls"),
                "component_before_hex": _component_hex(sweep, "before_hex"),
                "component_after_hex": _component_hex(sweep, "after_hex"),
                "component_scaled_hex": _component_hex(sweep, "scaled_hex"),
                "skipped": sweep.get("skipped"),
                "failed": sweep.get("failed"),
                "refused": sweep.get("refused"),
                "restore_bitexact": (
                    sweep.get("coupling_state_restore") or {}
                ).get("readback_bitexact"),
                "settings_restore_bitexact": (
                    sweep.get("settings_restore") or {}
                ).get("readback_bitexact"),
                "n_fields_put_back": sweep.get("n_fields_put_back"),
                "candidate_among_the_changed_fields": sweep.get(
                    "candidate_among_the_changed_fields"
                ),
                "candidate_set_to": sweep.get("candidate_set_to"),
            }
            for name, sweep in sweeps.items()
        },
    }
    row["restricted_from"] = restricted.get("computed_from")
    row["reproduces_the_record_audit"] = (
        row["sweeps"].get("output_entry_as_found", {}).get("residual_max_hex")
        == row["record_audit"]["residual_max_hex"]
    )
    return row


def _restore_diagnostics(observation: Mapping[str, Any]) -> dict[str, Any]:
    """What the whole-data-structure restore could not put back, by name.

    Two fields cannot be written back exactly, and both are named rather than
    counted away: one is serialised as a bare ``repr`` and cannot be rebuilt,
    the other does not read back equal.  Neither is read by a model, and the
    coupling-state restore — the one the residual is measured against — is
    bit-exact on every sweep, which is the property the audit depends on.
    """
    skipped: set[str] = set()
    mismatch: set[str] = set()
    coupling_bitexact = []
    settings_bitexact = []
    for sweep in observation.get("sweeps", []):
        structure = sweep.get("data_structure_restore") or {}
        skipped |= set(structure.get("skipped_repr") or ())
        mismatch |= set(structure.get("readback_mismatch_first") or ())
        coupling = sweep.get("coupling_state_restore")
        if coupling is not None:
            coupling_bitexact.append(bool(coupling.get("readback_bitexact")))
        settings = sweep.get("settings_restore")
        if settings is not None:
            settings_bitexact.append(bool(settings.get("readback_bitexact")))
    return {
        "data_structure_skipped_repr": sorted(skipped),
        "data_structure_readback_mismatch": sorted(mismatch),
        "coupling_state_restores_bitexact": (
            f"{sum(coupling_bitexact)}/{len(coupling_bitexact)}"
        ),
        "settings_restores_bitexact": (
            f"{sum(settings_bitexact)}/{len(settings_bitexact)}"
        ),
    }


def _restricted(audit, job, campaign, directory) -> dict[str, Any]:
    """The restricted exit-audit statistic, from the run's own residual vector.

    The optimisation record carries the whole-state audit; the **restricted**
    statistic — the components the per-run deferrable nodes write, excluded —
    is derived here from the run's committed residual vector plus the two
    committed artifacts that name the per-run nodes and what each node writes.
    That is the same derivation the harness uses inside a run, called with the
    per-run artifact stamped for the input file this job actually read.

    Carrying it inside the record belongs to the audit-restriction gate, which
    is another task's; until that lands this is where the number comes from,
    and it is the same derivation either way.
    """
    carried = audit.get("restricted") if isinstance(audit, dict) else None
    if carried:
        return dict(carried, computed_from="the run record")
    path = Path(directory) / "audit_residual.json"
    if not path.exists():
        return {"computed_from": None, "why": f"{path} is not there"}
    vector = json.loads(path.read_text())
    keys = list(vector["scaled"])
    values = [float(v) for v in vector["scaled"].values()]
    lifted = record_input_kind(job) == "lifted"
    summary, _excluded = child_mod.restricted_audit(
        job.config.per_run_artifact(lifted_input_file=lifted),
        job.config.name,
        Path(campaign.data_dir) / "node_writesets.json",
        keys,
        values,
        float(vector["tau"]),
    )
    return dict(
        summary,
        computed_from=(
            "this run's committed residual vector plus the committed per-run "
            "deferral artifact and write census"
        ),
    )


def record_input_kind(job) -> str:
    """Which input file this job read: the committed one, or the lifted copy."""
    arm = arms_mod.ARMS[job.arm]
    return "lifted" if arm.input_file == "lifted" and job.config.pulsed else "committed"


def _component_hex(sweep: Mapping[str, Any], field: str) -> str | None:
    for entry in sweep.get("head") or []:
        if entry.get("component") == COMPONENT:
            return entry.get(field)
    return None


def render(summary: Mapping[str, Any]) -> str:
    """The summary as the report's tables.  Captions included."""
    lines: list[str] = []
    lines.append(f"# Exit-audit diagnosis — `{COMPONENT}`\n")
    lines.append(
        f"Made {summary['made']} at `{summary['tree_git_head']}`; "
        f"{summary['n_rows']} of {summary['n_runs_declared']} declared runs "
        f"read, {summary['n_missing']} missing.\n"
    )

    lines.append("\n## The audit sweeps\n")
    lines.append(
        "*Caption: one row per run, one column per sweep of the declared "
        "series. Each cell is the maximum scaled residual of one further full "
        "sweep of the model set on the frozen ruler, as a hexadecimal float, "
        "with the component that held it. `as found` sweeps in the data "
        "structure the run was left in; `solve-phase map` puts back every "
        "data-structure field the output path changed. tau = 1e-6.*\n"
    )
    order = (
        ("output_entry_as_found", "as found"),
        ("output_entry_as_found_second_sweep", "as found, 2nd"),
        (
            "output_entry_with_the_solve_phase_settings",
            "solve-phase map",
        ),
        (
            "output_entry_with_the_solve_phase_settings_second_sweep",
            "solve-phase map, 2nd",
        ),
        (
            "output_entry_with_only_the_candidate_put_back",
            f"only `{audit_map_mod.CANDIDATE_FIELD}` put back",
        ),
        (
            "output_entry_without_the_candidate_put_back",
            "every other field put back",
        ),
        ("loop_exit_as_found", "loop exit, as found"),
        (
            "loop_exit_with_the_solve_phase_settings",
            "loop exit, solve-phase map",
        ),
    )
    lines.append(
        "| run | record audit (restricted) | "
        + " | ".join(label for _name, label in order)
        + " |"
    )
    lines.append("|---" * (2 + len(order)) + "|")
    for row in summary["rows"]:
        cells = [
            f"`{row['key']}`",
            f"{row['record_audit']['restricted_max_hex']} "
            f"(`{row['record_audit']['restricted_argmax']}`)",
        ]
        for name, _label in order:
            sweep = row["sweeps"].get(name, {})
            cells.append(
                f"{sweep.get('residual_max_hex')} (`{sweep.get('argmax')}`, "
                f"{sweep.get('n_above_tau')} above)"
            )
        lines.append("| " + " | ".join(cells) + " |")

    lines.append("\n## The component, and the setting the output path changes\n")
    lines.append(
        "*Caption: one row per run. `at the output entry` is the value of "
        f"`{COMPONENT}` in the state the solve handed over; `after one sweep "
        "as found` is what the audit's sweep makes of it. The last two columns "
        f"are the value of `{audit_map_mod.CANDIDATE_FIELD}` at those two "
        "moments — the radial-discretisation setting of the TF-coil stress "
        "calculation, which is not a coupling-state component and so is "
        "neither snapshotted nor restored.*\n"
    )
    lines.append(
        f"| run | `{COMPONENT}` at the output entry | after one sweep as found "
        "| relative change | scaled residual | setting at the entry | setting "
        "at the audit |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for row in summary["rows"]:
        sweep = row["sweeps"].get("output_entry_as_found", {})
        before_hex = sweep.get("component_before_hex")
        after_hex = sweep.get("component_after_hex")
        before = float.fromhex(before_hex) if before_hex else None
        after = float.fromhex(after_hex) if after_hex else None
        relative = (
            None
            if not before or after is None
            else abs(after - before) / abs(before)
        )
        setting = row.get("candidate_before_after") or {}
        lines.append(
            f"| `{row['key']}` | "
            + (f"{before:.10e} (`{before_hex}`)" if before is not None else "—")
            + " | "
            + (f"{after:.10e} (`{after_hex}`)" if after is not None else "—")
            + " | "
            + (f"{relative:.3%}" if relative is not None else "—")
            + f" | {sweep.get('residual_max_hex')} | {setting.get('before')} "
            f"| {setting.get('after')} |"
        )

    lines.append("\n## The dose response\n")
    lines.append(
        "*Caption: one row per run. Each column is one further sweep from the "
        "state the solve handed over, with "
        f"`{audit_map_mod.CANDIDATE_FIELD}` set to the named value and "
        "everything else as the run left it. The cell is the value of "
        f"`{COMPONENT}` after that sweep; the last row of each cell is the "
        "scaled residual the sweep reports. The solve ran at 100 throughout "
        "and the output path sets 500.*\n"
    )
    doses = (100, 200, 300, 400, 500)
    lines.append(
        "| run | " + " | ".join(f"at {value}" for value in doses) + " |"
    )
    lines.append("|---" * (1 + len(doses)) + "|")
    for row in summary["rows"]:
        cells = [f"`{row['key']}`"]
        for value in doses:
            sweep = row["sweeps"].get(
                f"output_entry_with_the_candidate_at_{value}", {}
            )
            after = sweep.get("component_after_hex")
            cells.append(
                (
                    f"{float.fromhex(after):.10e}<br>"
                    if after
                    else "component absent<br>"
                )
                + f"max {sweep.get('residual_max_hex')}"
            )
        lines.append("| " + " | ".join(cells) + " |")

    lines.append("\n## Is the audited state the loop's exit state?\n")
    lines.append(
        "*Caption: one row per run. Each cell is the number of coupling-state "
        "components that are not bit-identical between the two positions, over "
        "the configuration's whole component set.*\n"
    )
    pairs = (
        "last_sweep__vs__last_evaluation",
        "last_evaluation__vs__entry_to_write_output_files",
        "last_sweep__vs__entry_to_write_output_files",
        "entry_to_write_output_files__vs__before_finalise",
    )
    lines.append(
        "| run | last sweep → last evaluation | last evaluation → output entry "
        "| last sweep → output entry | output entry → before finalise |"
    )
    lines.append("|---|---|---|---|---|")
    for row in summary["rows"]:
        cells = [f"`{row['key']}`"]
        for pair in pairs:
            value = row["state_comparisons"].get(pair, {})
            cells.append(
                str(value.get("n_not_bit_identical"))
                if value.get("compared")
                else f"not compared ({value.get('why')})"
            )
        lines.append("| " + " | ".join(cells) + " |")

    lines.append("\n## What changed outside the coupling state\n")
    lines.append(
        "*Caption: one row per run. The population is every field of every "
        "namespace of the data structure; the count is those that differ "
        "between the entry to the output path and the moment the record's exit "
        "audit is taken, excluding the coupling-state components themselves.*\n"
    )
    lines.append(
        "| run | fields compared | differ, outside the coupling state | by "
        f"namespace | `{audit_map_mod.CANDIDATE_FIELD}` among them |"
    )
    lines.append("|---|---|---|---|---|")
    for row in summary["rows"]:
        value = row["data_structure"].get(
            "entry_to_write_output_files__vs__before_the_record_audit", {}
        )
        which = value.get("outside_the_coupling_state") or []
        by_namespace: dict[str, int] = {}
        for name in which:
            by_namespace[name.split(".", 1)[0]] = (
                by_namespace.get(name.split(".", 1)[0], 0) + 1
            )
        lines.append(
            f"| `{row['key']}` | {value.get('n_compared')} | "
            f"{value.get('n_outside_the_coupling_state')} | "
            + (
                ", ".join(
                    f"{namespace} {count}"
                    for namespace, count in sorted(by_namespace.items())
                )
                if which
                else "—"
            )
            + f" | {audit_map_mod.CANDIDATE_FIELD in which} |"
        )

    lines.append("\n## What the instrument could and could not put back\n")
    lines.append(
        "*Caption: one row per run. The coupling-state restore is the one the "
        "residual is measured against and is proved bit-exact on every sweep "
        "that takes one; the two named data-structure fields are what a whole-"
        "structure restore cannot reproduce, and neither is read by a model.*\n"
    )
    lines.append(
        "| run | coupling-state restores bit-exact | put-back restores "
        "bit-exact | not rebuildable | not equal on readback | last evaluation "
        "at the audited design point |"
    )
    lines.append("|---|---|---|---|---|---|")
    for row in summary["rows"]:
        diagnostics = row.get("restore_diagnostics") or {}
        identity = row.get("design_vector_identity") or {}
        lines.append(
            f"| `{row['key']}` | "
            f"{diagnostics.get('coupling_state_restores_bitexact')} | "
            f"{diagnostics.get('settings_restores_bitexact')} | "
            + (
                ", ".join(
                    f"`{n}`"
                    for n in diagnostics.get("data_structure_skipped_repr") or []
                )
                or "—"
            )
            + " | "
            + (
                ", ".join(
                    f"`{n}`"
                    for n in diagnostics.get("data_structure_readback_mismatch")
                    or []
                )
                or "—"
            )
            + f" | {identity.get('last_evaluation_is_the_audited_point')} "
            f"({identity.get('n_iteration_variables')} variables) |"
        )

    lines.append("\n## What the loop itself did\n")
    lines.append(
        "*Caption: one row per run, from the run record. The sweep histogram "
        "is sweeps of the node sequence per evaluation of the model set, over "
        "the solve phase only; its range is what the loop needed to reach the "
        "tolerance on every evaluation. Node calls are the solve phase's, the "
        "cost unit. The output-time loop's sweeps are counted separately and "
        "happen after the audit's declared position.*\n"
    )
    lines.append(
        "| run | ifail | optimiser iterations | evaluations | sweeps per "
        "evaluation | node calls, solve phase | output path | output-time "
        "sweeps |"
    )
    lines.append("|---|---|---|---|---|---|---|---|")
    for row in summary["rows"]:
        histogram = (row.get("sweeps_per_eval") or {}).get("hist") or {}
        bins = sorted(int(k) for k in histogram)
        lines.append(
            f"| `{row['key']}` | {row.get('ifail')} | "
            f"{row.get('n_solver_iterations')} | "
            f"{(row.get('sweeps_per_eval') or {}).get('n_evaluations')} | "
            + (f"{bins[0]}–{bins[-1]}" if bins else "—")
            + f" | {row.get('node_calls_solve_phase')} | "
            f"`{row.get('output_path')}` | {row.get('output_loop_sweeps')} |"
        )
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# the entry point
# --------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "stage", choices=("census", "runs", "report", "all"), nargs="?", default="all"
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--only",
        action="append",
        default=None,
        metavar="CONFIGURATION/ARM/seedNNN",
        help="narrow the declared run set to these keys; never adds a run",
    )
    args = parser.parse_args(argv)

    campaign = default_campaign()
    if not campaign.is_experiment_copy:
        print(
            f"refusing: {campaign.tree} is not the experiment's own copy of "
            f"PROCESS",
            file=sys.stderr,
        )
        return 3
    root(campaign).mkdir(parents=True, exist_ok=True)

    if args.stage in {"census", "all"}:
        record = census(campaign)
        path = root(campaign) / "census.json"
        path.write_text(json.dumps(record, indent=2, default=str) + "\n")
        print(f"census written to {path}")
        for name, row in record["configurations"].items():
            print(
                f"  {name:24s} writers={row['writers']} "
                f"category={row.get('category')} scale={row.get('scale')}"
            )
    if args.stage in {"runs", "all"}:
        manifest = make_runs(campaign, resume=args.resume, only=args.only)
        print(f"{manifest['n_runs']} runs; manifest {manifest['manifest']}")
    if args.stage in {"report", "all"}:
        summary = summarise(campaign, only=args.only)
        print(render(summary))
        if summary["n_missing"]:
            print(
                f"{summary['n_missing']} declared run(s) have no observation: "
                f"{[m['key'] for m in summary['missing']]}",
                file=sys.stderr,
            )
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
