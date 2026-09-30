"""The exclusion sets of every record-comparing gate, reviewed -- a measurement stage.

Every exclusion of gate G1 (``switch_neutrality``), classified by kind and
measured against that gate's own captured records: how many leaves each name
covers on each side, whether both sides carry them, and what this review did
with the name.  It reads the tables from the gate module -- ``gate_neutrality``
-- and never restates them, so a name added to a gate is a name this review
sees.  (Gate G8's part was removed with the gate under V5 list item 10; G1's
part is kept, plan §11 row 10.)

Moved verbatim out of ``harness/gates/gates.py`` (its ``the exclusion sets,
reviewed`` section) by the code-move task of the simplification survey, into
its own module because it reads three gates' tables and can sit inside none of
them without an import cycle; written by task **A52 (harness-gates)**.  Stage
name and record path are unchanged; it is registered in
``harness/gates/registry.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

_EXPERIMENT_DIR = Path(__file__).resolve().parents[2]
if str(_EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENT_DIR))

from harness.core import framework  # noqa: E402
from harness.core.config import Campaign  # noqa: E402
from harness.gates.gate_neutrality import (  # noqa: E402
    ALWAYS_EXCLUDED,
    FIELDS_ADDED_BY_A_DRIVER_CHANGE,
    FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE,
    INSTRUMENT_CHANGE_KIND,
    NEUTRAL_ARMS,
    VOLATILE_MFILE_KEYS,
    VOLATILE_RECORD_PATHS,
    _read_record,
    _same,
    _straddle,
    compare_records,
    exit_audit_instrument,
    is_volatile,
    leaves,
    neutrality_root,
    neutrality_run_dir,
)
from harness.gates.gate_output_path import UNCHANGED_ON_REFERENCE_ARMS  # noqa: E402

GateError = framework.GateError


# --------------------------------------------------------------------------
# the exclusion sets, reviewed
# --------------------------------------------------------------------------
#
# Three gates compare two records value by value and each names the leaves it
# does not compare.  A named exclusion is the right shape — a zero over a
# population quietly smaller than the one stated is this project's trap T11 —
# but a list of names that only ever grows is the same failure a step later, so
# task **A52 (harness-gates)** was asked to review all three as one thing rather
# than extend them.
#
# The review is a *measurement*, not an opinion.  For every excluded name it
# reads the gate's own captured records and reports how many leaves the name
# covers on each side, whether both sides carry them, and whether they are
# equal — so "could this be compared instead?" is answered from the records.
#
# What the measurement cannot answer on its own is **why** a name is equal here.
# `tree_git_head` is equal whenever the two captures happen to be at one commit
# and differs the moment they are not; that is a property of the run, not of the
# field.  So each name also carries a declared *kind*, and the two together are
# what the verdict rests on: a structural kind stays excluded however equal it
# reads today, and a "field a change adds" is excluded only where one side
# actually lacks it.

#: Why each always-excluded name can never be compared.  Every name in
#: :data:`ALWAYS_EXCLUDED` must appear here — a name with no declared kind
#: raises at import, because an exclusion nobody classified is an exclusion
#: nobody reviewed.
ALWAYS_EXCLUDED_KIND: dict[str, str] = {
    "outdir": "a path",
    "campaign_input_file": "a path",
    "entry_state": "a path",
    "exit_audit.coupling_state": "a path",
    "exit_audit.restricted.artifact": "a path",
    "exit_audit.restricted.census": "a path",
    "per_run_artifact": "a path",
    "process_copy_provenance.path": "a path",
    "coupling_state_artifact": "a path",
    "coupling_state_provenance.path": "a path",
    "exit_audit.frozen.restricted.artifact": "a path",
    "exit_audit.frozen.restricted.census": "a path",
    "exit_audit.mixed.restricted.artifact": "a path",
    "exit_audit.mixed.restricted.census": "a path",
    "tree_git_branch": "the commit, or the working tree's state",
    "pythonpath": "a path",
    "tree": "a path",
    "repository": "a path",
    "process_file": "a path",
    "launcher": "a timing or the machine's state",
    "wall_s": "a timing or the machine's state",
    "cpu_user_s": "a timing or the machine's state",
    "cpu_sys_s": "a timing or the machine's state",
    "cpu_s": "a timing or the machine's state",
    "maxrss_kb": "a timing or the machine's state",
    "loadavg": "a timing or the machine's state",
    "mfile.process_runtime": "a timing or the machine's state",
    "tree_git_head": "the commit, or the working tree's state",
    "tree_git_describe": "the commit, or the working tree's state",
    "tree_modified_tracked": "the commit, or the working tree's state",
    "tree_untracked_paths": "the commit, or the working tree's state",
    "tree_modified_tracked_n": "the commit, or the working tree's state",
    "tree_untracked_paths_n": "the commit, or the working tree's state",
    "tree_git_dirty": "the commit, or the working tree's state",
    "process_copy_provenance.copy_date": "the commit, or the working tree's state",
    "env_architecture": "the switch vocabulary the change renames",
    "resolved_switches": "the switch vocabulary the change renames",
    "audit_position_note": "prose quoted from a harness constant",
    # A100 (v5-test-set), DR11: the harness's stamps of itself and of the
    # campaign it was pressed from (see gate_neutrality.ALWAYS_EXCLUDED).
    "harness_version": "the harness's own version stamp",
    "campaign_tau": "the campaign's declared setting, a harness stamp",
    "campaign_test_set": "the campaign's declared setting, a harness stamp",
    "exit_audit.rulers_note": "prose quoted from a harness constant",
    # A102 (v5-campaign): the warmed evaluation child's own wall-clock leaves.
    "evaluation_warmup.warmup.wall_s": "a timing or the machine's state",
    "evaluation_warmup.measured.wall_s": "a timing or the machine's state",
    "evaluation_warmup.warmup.timers_driver": "a timing or the machine's state",
    "evaluation_warmup.restore_wall_s": "a timing or the machine's state",
    "evaluation_warmup.warmup_wall_s": "a timing or the machine's state",
}

def _assert_every_name_is_classified() -> None:
    missing = sorted(set(ALWAYS_EXCLUDED) - set(ALWAYS_EXCLUDED_KIND))
    if missing:
        raise GateError(
            f"{len(missing)} always-excluded name(s) carry no declared kind: "
            f"{missing}.  An exclusion nobody classified is an exclusion "
            f"nobody reviewed."
        )
    spare = sorted(set(ALWAYS_EXCLUDED_KIND) - set(ALWAYS_EXCLUDED))
    if spare:
        raise GateError(
            f"{len(spare)} classified name(s) are not excluded at all: {spare}"
        )
    missing = sorted(
        set(FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE) - set(INSTRUMENT_CHANGE_KIND)
    )
    if missing:
        raise GateError(
            f"{len(missing)} name(s) excluded across an instrument change "
            f"carry no declared kind: {missing}"
        )
    spare = sorted(
        set(INSTRUMENT_CHANGE_KIND) - set(FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE)
    )
    if spare:
        raise GateError(
            f"{len(spare)} classified name(s) are not excluded at all: {spare}"
        )


_assert_every_name_is_classified()


def _coverage(
    name: str,
    pairs: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]],
    *,
    also_excluded: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """How many leaves *name* covers on each side, and whether they agree.

    ``also_excluded`` names leaves another exclusion already covers, so that a
    conditional name is not credited with leaves a structural one takes out
    anyway — the two absolute paths inside the restricted statistic are the live
    case, and counting them here would overstate what this review put back into
    the comparison by twelve.
    """
    table = {name: "under review"}
    on_a = on_b = both = equal = 0
    for before, after in pairs:
        a, b = leaves(dict(before)), leaves(dict(after))
        for path in sorted(set(a) | set(b)):
            if is_volatile(path, table) is None:
                continue
            if also_excluded and is_volatile(path, also_excluded) is not None:
                continue
            in_a, in_b = path in a, path in b
            on_a += int(in_a)
            on_b += int(in_b)
            if in_a and in_b:
                both += 1
                va, vb = a[path], b[path]
                if _same(va, vb) and (va is None) == (vb is None):
                    equal += 1
    return {
        "leaves_before": on_a,
        "leaves_after": on_b,
        "leaves_on_both_sides": both,
        "leaves_equal_where_both_sides_have_them": equal,
        "present_on_both_sides_everywhere": both == on_a == on_b and both > 0,
        "equal_everywhere_it_is_present": both > 0 and equal == both,
    }


def _neutrality_pairs(campaign: Campaign) -> list[tuple[dict, dict]]:
    pairs: list[tuple[dict, dict]] = []
    for phase, arm in NEUTRAL_ARMS:
        for config in campaign.configurations:
            key = f"{arm}/{config.name}"
            before_dir = neutrality_run_dir(campaign, "before", config.name, arm)
            after_dir = neutrality_run_dir(campaign, "after", config.name, arm)
            if not (before_dir / "metrics.json").exists():
                continue
            if not (after_dir / "metrics.json").exists():
                continue
            pairs.append(
                (
                    _read_record(before_dir, side="before", key=key),
                    _read_record(after_dir, side="after", key=key),
                )
            )
    return pairs


def exclusion_review(campaign: Campaign) -> dict[str, Any]:
    """Every exclusion of every comparing gate, classified and measured.

    Three tables, each a row per excluded name: what kind of thing it is, why
    it is excluded, how many leaves it covers on each side of the gate's own
    captured records, whether both sides carry them and whether they agree, and
    the verdict — kept, made conditional, or removed.
    """
    g1_pairs = _neutrality_pairs(campaign)
    # **Which pair of commits gate G1's captures straddle changes the answer**,
    # and a leaf count published without it is a number without its condition
    # (trap T11).  A name that is one-sided across a real straddle is excluded
    # there and compared in a self-comparison, so "how many leaves did making
    # these conditional put back?" has one answer per pairing.
    g1_straddle = _straddle(
        neutrality_root(campaign) / "before" / "manifest.json",
        neutrality_root(campaign) / "after" / "manifest.json",
    )

    g1_rows: list[dict[str, Any]] = []
    for name, reason in ALWAYS_EXCLUDED.items():
        coverage = _coverage(name, g1_pairs)
        g1_rows.append(
            {
                "name": name,
                "group": "always excluded",
                "kind": ALWAYS_EXCLUDED_KIND[name],
                "reason": reason,
                **coverage,
                "could_be_compared_instead": False,
                "verdict": (
                    "KEPT — the kind is structural: it reads equal here only "
                    "because these two captures happen to agree on it, and a "
                    "later pair would not"
                    if coverage["equal_everywhere_it_is_present"]
                    else "KEPT — it differs on the captures, as its reason says"
                ),
            }
        )
    for name, reason in FIELDS_ADDED_BY_A_DRIVER_CHANGE.items():
        coverage = _coverage(name, g1_pairs, also_excluded=ALWAYS_EXCLUDED)
        compared_here = coverage["present_on_both_sides_everywhere"]
        g1_rows.append(
            {
                "name": name,
                "group": "excluded only where one side lacks the field",
                "kind": "a field a change adds (null or absent before, a value after)",
                "reason": reason,
                **coverage,
                "could_be_compared_instead": compared_here,
                "verdict": (
                    "COMPARED at this commit — both sides carry it, so the "
                    "condition does not fire and the field is in the "
                    "comparison"
                    if compared_here
                    else (
                        "INERT at this commit — the name matches no leaf on "
                        "either side, so it excludes nothing.  It is kept "
                        "because the field it names appears exactly when a "
                        "driver stamps nothing at a boundary, which is the "
                        "case it exists for"
                        if coverage["leaves_before"] == 0
                        and coverage["leaves_after"] == 0
                        else "EXCLUDED at this commit — one side lacks the field"
                    )
                ),
            }
        )

    # Whether the pairing this review measures over actually straddles an
    # instrument change decides what the rows below mean, exactly as the
    # commit pairing does for the two groups above.  It is read off the
    # captured records, not assumed.
    instruments_differ = any(
        exit_audit_instrument(before) != exit_audit_instrument(after)
        for before, after in g1_pairs
    )
    for name, reason in FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE.items():
        coverage = _coverage(name, g1_pairs, also_excluded=ALWAYS_EXCLUDED)
        g1_rows.append(
            {
                "name": name,
                "group": (
                    "excluded only where the two records' exit-audit "
                    "instruments differ"
                ),
                "kind": INSTRUMENT_CHANGE_KIND[name],
                "reason": reason,
                **coverage,
                "could_be_compared_instead": not instruments_differ,
                "verdict": (
                    "EXCLUDED at this pairing — the two captures' exit audits "
                    "were taken by different instruments, so this leaf is a "
                    "measurement by two rulers and not a difference in "
                    "behaviour"
                    if instruments_differ
                    else (
                        "COMPARED at this pairing — both captures name the "
                        "same instrument, so the condition does not fire and "
                        "the leaf is in the comparison"
                        if coverage["leaves_on_both_sides"]
                        else "INERT at this pairing — the name matches no leaf "
                        "on either side"
                    )
                ),
            }
        )

    # Where the instrument exclusion's leaves actually are.  The group's whole
    # claim is that it takes out the audit's residual and the instrument's own
    # account of itself, and **nothing else** — so the leaves it removes are
    # counted by prefix rather than asserted to be where they should be.  A
    # leaf outside the exit audit and its stamp would mean the group is hiding
    # something it was not written for, and the count says so by name.
    instrument_leaves: dict[str, int] = {}
    for before, after in g1_pairs:
        result = compare_records(
            before,
            after,
            excluded=ALWAYS_EXCLUDED,
            conditional=FIELDS_ADDED_BY_A_DRIVER_CHANGE,
            instrument_changed=FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE,
        )
        for path in result["excluded_by_the_instrument_change"]:
            head = path.split("[")[0]
            prefix = (
                "exit_audit.instrument"
                if head.startswith("exit_audit.instrument")
                else "exit_audit."
                if head.startswith("exit_audit.")
                else head.split(".")[0]
            )
            instrument_leaves[prefix] = instrument_leaves.get(prefix, 0) + 1
    outside = {
        prefix: count
        for prefix, count in instrument_leaves.items()
        if not prefix.startswith("exit_audit")
        and prefix not in {"audit_snapshot"}
    }

    g9_rows = [
        {
            "name": name,
            "group": "compared",
            "kind": "a field that describes the solve",
            "reason": (
                "compared against the reproduction gate's record for the same "
                "run: 'nothing changes on the arms that keep the loop' is a "
                "comparison, not an assertion"
            ),
            "verdict": "COMPARED",
        }
        for name in UNCHANGED_ON_REFERENCE_ARMS
    ] + [
        {
            "name": "exit_audit.residual_max_hex",
            "group": "deliberately absent from the compared list",
            "kind": "a field the same change moved for every arm",
            "reason": (
                "the audit position moved to the plan's declared position for "
                "every arm in the same change, so the residual is expected to "
                "differ and comparing it would test the audit rather than the "
                "output path"
            ),
            "could_be_compared_instead": False,
            "verdict": (
                "KEPT ABSENT — and the position itself is compared instead: "
                "every row checks that the audit was taken where the plan "
                "declares"
            ),
        }
    ]

    conditional_compared = sum(
        row["leaves_on_both_sides"]
        for row in g1_rows
        if row["group"].startswith("excluded only")
        and row["could_be_compared_instead"]
    )
    return {
        "what_this_is": (
            "every exclusion of every gate that compares two records, "
            "classified by kind and measured against that gate's own captured "
            "records"
        ),
        "caption": (
            "One row per excluded name. 'kind' is what sort of thing it is; "
            "'leaves before/after' is how many record leaves the name covers "
            "on each side of the gate's captured pairs, summed over every "
            "pair; 'equal where both have them' is how many of those agree. "
            "The verdict is what this review did with the name. Populations: "
            f"gate G1 over {len(g1_pairs)} run pair(s) which {g1_straddle['says']} "
            f"— the leaf counts below hold for that pairing and no other; "
            f"gate G9's list is a list of fields "
            "it compares, not of fields it excludes, and is shown for the same "
            "reason."
        ),
        "G1_pairing": g1_straddle,
        "G1_instrument_leaves_by_prefix": {
            "what": (
                "every record leaf the instrument-change group removed from "
                "gate G1's comparison, counted by where it sits.  The group's "
                "claim is that it takes out the audit's residual and the "
                "instrument's own account of itself and nothing else; this is "
                "the measurement of that claim rather than the assertion"
            ),
            "by_prefix": dict(sorted(instrument_leaves.items())),
            "n_leaves": sum(instrument_leaves.values()),
            "n_outside_the_audit_and_its_stamp": sum(outside.values()),
            "outside_the_audit_and_its_stamp": dict(sorted(outside.items())),
            "none_outside_the_audit_and_its_stamp": not outside,
        },
        "G1_instrument_pairing": {
            "instruments": sorted(
                {
                    str(exit_audit_instrument(record))
                    for pair in g1_pairs
                    for record in pair
                }
            ),
            "straddles_an_instrument_change": instruments_differ,
            "says": (
                "the two captures' exit audits were taken by different "
                "instruments, so the third group's names are excluded here "
                "and compared at any pairing where the stamps agree"
                if instruments_differ
                else "both captures name the same exit-audit instrument, so "
                "the third group excludes nothing here"
            ),
        },
        "sizes": {
            "G1_before_this_review": len(VOLATILE_RECORD_PATHS),
            "G1_after_this_review": len(ALWAYS_EXCLUDED),
            "G1_conditional": len(FIELDS_ADDED_BY_A_DRIVER_CHANGE),
            "G1_conditional_on_the_instrument": len(
                FIELDS_CHANGED_BY_AN_INSTRUMENT_CHANGE
            ),
            "G1_output_file_keys": len(VOLATILE_MFILE_KEYS),
            "G9_fields_compared": len(UNCHANGED_ON_REFERENCE_ARMS),
            "G9_fields_deliberately_absent": 1,
        },
        "what_the_review_changed": (
            f"gate G1's set was {len(VOLATILE_RECORD_PATHS)} names, every one "
            f"excluded unconditionally.  {len(ALWAYS_EXCLUDED)} of them are "
            f"structural — a path, a timing, the machine's state, the commit, "
            f"or the switch vocabulary a rename changes — and stay excluded "
            f"however equal they read.  The other "
            f"{len(FIELDS_ADDED_BY_A_DRIVER_CHANGE)} were excluded because "
            f"**one particular pair of commits** straddled the change that "
            f"added the field; they are now excluded only where one side "
            f"actually lacks the field, and compared wherever both sides carry "
            f"it.  Over the pairing measured here — {g1_straddle['says']} — "
            f"that puts {conditional_compared} further leaves back into the "
            f"comparison, and the count is a property of the pairing, not of "
            f"the table.  Nothing was removed from the "
            f"table: a name that stops being needed is worth more visible than "
            f"deleted, and the condition is what makes it inert."
        ),
        "G1": {
            "gate": "switch_neutrality",
            "population": f"{len(g1_pairs)} run pair(s)",
            "rows": g1_rows,
        },
        "G9": {
            "gate": "output_path",
            "population": "the fields compared against the reproduction gate",
            "rows": g9_rows,
        },
    }


def print_exclusion_review(block: Mapping[str, Any]) -> None:
    print(f"\n  {block['what_this_is']}")
    print(f"\n  {block['caption']}")
    print(f"\n  {block['what_the_review_changed']}\n")
    for key in ("G1", "G9"):
        table = block[key]
        print(f"\n  --- {key} ({table['gate']}) — {table['population']}")
        print(
            f"    {'name':<52} {'kind':<48} {'before':>7} {'after':>7} "
            f"{'equal':>7}  verdict"
        )
        for row in table["rows"]:
            print(
                f"    {row['name']:<52} {row['kind']:<48} "
                f"{str(row.get('leaves_before', '-')):>7} "
                f"{str(row.get('leaves_after', '-')):>7} "
                f"{str(row.get('leaves_equal_where_both_sides_have_them', '-')):>7}"
                f"  {row['verdict'].split(' — ')[0]}"
            )
    leaves = block.get("G1_instrument_leaves_by_prefix")
    if leaves:
        print(
            f"\n  instrument-change leaves, by prefix "
            f"({leaves['n_leaves']} in all; "
            f"{leaves['n_outside_the_audit_and_its_stamp']} outside the exit "
            f"audit and its stamp):"
        )
        for prefix, count in leaves["by_prefix"].items():
            print(f"    {prefix:<34} {count}")
    sizes = block["sizes"]
    print("\n  sizes:")
    for name, value in sizes.items():
        print(f"    {name:<34} {value}")




