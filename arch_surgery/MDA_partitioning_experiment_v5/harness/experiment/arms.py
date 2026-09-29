"""The experiment's switch matrix as data, and the environments it composes.

Transcribes EXPERIMENT_REPORT.md §3.2 — the matrix and the rung table — one
field per matrix row.  Derived from
``arch_surgery/MDA_partitioning_experiment_v3/v3_runner.py::env_for`` and
``arch_surgery/MDA_partitioning_experiment_v3/phase_a.py::env_for_phase_a`` at
``f2dc9243`` (task A47), which were two separate chains of ``if`` statements
over the same vocabulary and had already drifted apart in two places.  Here
there is one composition, and the difference between two arms is a computed
field difference rather than a sentence in a docstring.

Three functions are public: :func:`env_for` builds an arm's environment from
nothing, :func:`input_file_for` says which input file it reads, and
:func:`rung` says what changes between two arms.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Mapping

from . import switches
from ..core.config import Campaign, Config, default_campaign
from .switches import SwitchError

# --------------------------------------------------------------------------
# one arm = one column of the matrix
# --------------------------------------------------------------------------

#: The matrix's independent rows, in the plan's order.  Four further rows of
#: EXPERIMENT_REPORT.md §3.2 — the stopping rule, the number of schedule passes,
#: whether the burn time is out of the loop, and which input file is read —
#: are not listed here because they are not choices: each follows from a field
#: below, and :data:`PLAN_MATRIX` is regenerated from these to prove it.
MATRIX_FIELDS: tuple[str, ...] = (
    "mda",
    "arrangement_node",
    "arrangement_method",
    "defer_per_call",
    "defer_per_run",
    "burn_time_owner",
    "output_loop",
)


@dataclass(frozen=True)
class Arm:
    """One assignment of the driver's switches: one column of the matrix."""

    name: str
    #: "A" (one evaluation of the model set) or "B" (one optimisation).
    phase: str
    #: "upstream" | "flat" | "partitioned" — the shape of the analysis loop.
    mda: str
    #: 'build' runs after 'physics'.
    arrangement_node: bool
    #: The first-wall geometry method runs at the head of every sweep.
    arrangement_method: bool
    #: Feed-forward nodes run once per evaluation instead of once per sweep.
    defer_per_call: bool
    #: Optimiser-irrelevant nodes run once per run, at the accepted optimum.
    defer_per_run: bool
    #: Who owns the burn time on a pulsed configuration: "loop" | "constant" |
    #: "optimiser".  On a steady-state configuration there is no burn-time
    #: coupling and the field has no effect.
    burn_time_owner: str
    #: "upstream" | "none", or None where the row does not apply.  Whether the
    #: run re-solves the accepted state through upstream's output-time loop
    #: before writing its files.  A Phase A arm evaluates the model set once
    #: and never reaches the output path, so it carries **no switch for this
    #: at all** and the matrix row reads ``n/a`` for it.
    output_loop: str | None
    #: Why this arm is in the experiment (one sentence, for the README and
    #: for a refusal message).
    role: str

    # --- rows of the plan's matrix that follow from the fields above ------

    @property
    def stopping_rule(self) -> str:
        """What ends the analysis loop."""
        return "objf/conf" if self.mda == "upstream" else "y @ τ"

    @property
    def schedule_passes(self) -> str:
        """How often the block schedule runs: not a choice, a consequence.

        It composes **no switch**.  The driver used to take a separate setting
        for it and this property used to be the value of that setting; since
        the rename, choosing the partitioned loop *is* choosing to run the
        schedule once, and the old switch name raises if anything sets it.
        The property survives because the plan's matrix has a row for it.
        """
        if self.mda == "upstream":
            return "none"
        return "once" if self.mda == "partitioned" else "single block"

    @property
    def burn_time_out_of_loop(self) -> bool:
        return self.burn_time_owner != "loop"

    @property
    def input_file(self) -> str:
        """"committed" or "lifted" — which input file the arm reads."""
        return "lifted" if self.burn_time_owner == "optimiser" else "committed"

    @property
    def is_reference(self) -> bool:
        """PROCESS as shipped: every architecture switch unset."""
        return self.mda == "upstream"

    def loop_key(self, config: Config) -> str:
        """The key the driver selects this arm's census test sets by.

        ``<mda>/<burn-time owner>`` as the driver resolves them
        (``module_solve.MDA_MODE`` and ``subsolve.BURN_TIME_OWNER``): the
        driver never knows an arm's name, and that pair is what tells the
        loops the census measured apart.  On a steady-state configuration no
        owner is composed and the driver resolves ``loop``.
        """
        owner = self.burn_time_owner if (config.pulsed and self.burn_time_out_of_loop) else "loop"
        return f"{self.mda}/{owner}"

    # --- composition ------------------------------------------------------

    def terms(
        self,
        config: Config,
        *,
        pin_hex: str | None = None,
        predicate_mode: str = "frozen",
        campaign: Campaign | None = None,
        seed: int | None = None,
        test_set: str | None = None,
        tau: float | None = None,
    ) -> dict[str, str]:
        """The switch terms this arm sets on *config*, term -> value.

        The single place an arm becomes switch settings.  Terms are V4's
        words; ``switches.REGISTRY`` turns each into the variable name the
        tree implements, so a rename touches one file.

        ``test_set`` and ``tau`` default to the campaign's (DR11: one test set
        and one tolerance per campaign, D39 and D23); the pool passes a job's
        own where a declared supplementary stage admits other values.
        """
        campaign = campaign or default_campaign()
        if self.is_reference:
            return {}

        test_set = campaign.test_set if test_set is None else test_set
        tau = campaign.tau if tau is None else tau
        lifted_here = config.pulsed and self.burn_time_out_of_loop
        terms: dict[str, str] = {
            "mda": self.mda,
            "tolerance": repr(float(tau)),
            "coupling_state": str(config.coupling_state_path),
            "write_sets": str(config.write_sets_path),
            # DR11: which components every block loop tests, and — under the
            # census set — the artifact naming them for this configuration.
            "test_set": test_set,
        }
        if test_set == "census":
            terms["test_sets"] = str(config.test_sets_path)
        if self.arrangement_node:
            terms["arrangement_node"] = "build_after_physics"
        if self.arrangement_method:
            terms["arrangement_method"] = "fw_geometry"
        if self.defer_per_call:
            # 'feedforward_lifted' additionally defers the burn-time node,
            # which is only correct once that site has left the loop; the
            # driver refuses the pair the other way round.
            terms["defer_per_call"] = (
                "feedforward_lifted" if lifted_here else "feedforward"
            )
        if self.defer_per_run:
            terms["defer_per_run"] = str(
                config.per_run_artifact(
                    lifted_input_file=self.input_file == "lifted"
                )
            )
            if self.phase == "A":
                # V5 list item 5 (A101 (v5-timers-and-once); decision D35):
                # an evaluation-phase run is one call_models and never
                # reaches the output path, so the deferred set is executed
                # once at the evaluation's exit instead -- the MDA converged,
                # then every deferred node once.  Not a matrix row: it
                # follows from the phase and the deferral.  The optimisation
                # phase leaves the switch unset and executes the set at the
                # output path as before.
                terms["defer_per_run_execution"] = "evaluation_exit"
        if lifted_here:
            # One switch says who owns the burn time.  The two settings this
            # replaces could disagree with each other -- a constant owning a
            # quantity the model still solved for -- and that combination can
            # no longer be written down.
            if self.burn_time_owner == "constant":
                if pin_hex is None:
                    raise SwitchError(
                        f"{self.name} on pulsed configuration {config.name} "
                        f"names a constant as the burn time's owner"
                        + (f" (seed {seed})" if seed is not None else "")
                        + ": running it without that constant would leave the "
                        f"loop owning the variable and measure a different arm"
                    )
                terms["burn_time_owner"] = f"constant:{pin_hex}"
            else:
                terms["burn_time_owner"] = self.burn_time_owner
        if self.output_loop == "none":
            terms["output_loop"] = "none"
        if predicate_mode != campaign.predicate_mode_default:
            if predicate_mode not in campaign.predicate_modes:
                raise SwitchError(
                    f"predicate mode {predicate_mode!r} is not one of "
                    f"{campaign.predicate_modes}"
                )
            terms["predicate_mode"] = predicate_mode
        return terms


#: The eight arms of EXPERIMENT_REPORT.md §3.2, named so that the two phases
#: read rung for rung: ``AR/A0/A1/A2`` against ``BR/B0/B1/B2`` — the reference,
#: the flat control, the ownership rung, the partition.  **Renamed 2026-09-15**
#: at the user's ruling (*"rename … so the naming of the rungs reflects the
#: parallelism in the switch matrix"*); the two Phase A arms after the control
#: and the partitioned optimisation arm changed name, and the one table that
#: says from what — ``records.RECORDED_ARM_NAMES`` — is the one place the old
#: names are spelled.  Records made before that date carry the old names and
#: are read through it.
#:
#: V3's joint-test arm — V3's ``B2``, which repeated the block schedule — is
#: **not** in V4 (D22, the user's ruling of 2026-09-10): its verification pass
#: was measured triggering a third pass zero times in 91 888 calls.  Today's
#: ``B2`` is a different arm, the partitioned optimisation arm; the shared
#: spelling is V3's alone to carry, and every mention of the removed arm says
#: "V3's ``B2``".
ARMS: dict[str, Arm] = {
    "AR": Arm(
        name="AR",
        phase="A",
        mda="upstream",
        arrangement_node=False,
        arrangement_method=False,
        defer_per_call=False,
        defer_per_run=False,
        burn_time_owner="loop",
        output_loop=None,  # Phase A never reaches the output path
        role=(
            "PROCESS as shipped, one evaluation: says where upstream's own "
            "stopping rule leaves the coupling state"
        ),
    ),
    "A0": Arm(
        name="A0",
        phase="A",
        mda="flat",
        arrangement_node=False,
        arrangement_method=False,
        defer_per_call=False,
        defer_per_run=False,
        burn_time_owner="loop",
        output_loop=None,  # Phase A never reaches the output path
        role=(
            "the flat control: one block over every in-loop node, stopped on "
            "the coupling state at the shared tolerance"
        ),
    ),
    "A1": Arm(
        name="A1",
        phase="A",
        mda="flat",
        arrangement_node=False,
        arrangement_method=False,
        defer_per_call=False,
        defer_per_run=False,
        burn_time_owner="constant",
        output_loop=None,  # Phase A never reaches the output path
        role=(
            "the flat control with the burn time owned by a constant: the "
            "ownership rung, with nothing else changed"
        ),
    ),
    "A2": Arm(
        name="A2",
        phase="A",
        mda="partitioned",
        arrangement_node=True,
        arrangement_method=True,
        defer_per_call=True,
        defer_per_run=True,
        burn_time_owner="constant",
        output_loop=None,  # Phase A never reaches the output path
        role="the partitioned architecture, one evaluation: Phase A's headline",
    ),
    "BR": Arm(
        name="BR",
        phase="B",
        mda="upstream",
        arrangement_node=False,
        arrangement_method=False,
        defer_per_call=False,
        defer_per_run=False,
        burn_time_owner="loop",
        output_loop="upstream",
        role="PROCESS as shipped, one optimisation: the user-facing reference",
    ),
    "B0": Arm(
        name="B0",
        phase="B",
        mda="flat",
        arrangement_node=False,
        arrangement_method=False,
        defer_per_call=False,
        defer_per_run=False,
        burn_time_owner="loop",
        output_loop="upstream",
        role="the flat control, and the designed comparison's baseline",
    ),
    "B1": Arm(
        name="B1",
        phase="B",
        mda="flat",
        arrangement_node=False,
        arrangement_method=False,
        defer_per_call=False,
        defer_per_run=False,
        burn_time_owner="optimiser",
        output_loop="none",
        role=(
            "the flat control with the optimiser owning the burn time: the "
            "ownership rung in the phase that has an optimiser"
        ),
    ),
    "B2": Arm(
        name="B2",
        phase="B",
        mda="partitioned",
        arrangement_node=True,
        arrangement_method=True,
        defer_per_call=True,
        defer_per_run=True,
        burn_time_owner="optimiser",
        output_loop="none",
        role="the partitioned architecture, optimised: Phase B's headline",
    ),
}

PHASE_A_ARMS: tuple[str, ...] = tuple(n for n, a in ARMS.items() if a.phase == "A")
PHASE_B_ARMS: tuple[str, ...] = tuple(n for n, a in ARMS.items() if a.phase == "B")


# --------------------------------------------------------------------------
# the plan's table, transcribed for comparison
# --------------------------------------------------------------------------

#: EXPERIMENT_REPORT.md §3.2's matrix, cell for cell, as the plan prints it.
#: :func:`matrix_cell` regenerates each cell from :data:`ARMS`; the two are
#: compared by the self-check, so a transcription slip is caught rather than
#: carried into every run of the campaign.
MATRIX_ORDER = ("AR", "A0", "A1", "A2", "BR", "B0", "B1", "B2")

PLAN_MATRIX: dict[str, tuple[str, ...]] = {
    "MDA solve": ("upstream", "flat", "flat", "partitioned",
                  "upstream", "flat", "flat", "partitioned"),
    "stopping rule": ("objf/conf", "y @ τ", "y @ τ", "y @ τ",
                      "objf/conf", "y @ τ", "y @ τ", "y @ τ"),
    "block schedule": ("—", "(one block)", "(one block)", "one pass",
                       "—", "(one block)", "(one block)", "one pass"),
    "arrangement · node (build after physics)": ("—", "—", "—", "✓",
                                                 "—", "—", "—", "✓"),
    "arrangement · method (prime)": ("—", "—", "—", "✓", "—", "—", "—", "✓"),
    "deferral per_call": ("—", "—", "—", "✓", "—", "—", "—", "✓"),
    "deferral per_run": ("—", "—", "—", "✓", "—", "—", "—", "✓"),
    "burn time out of the loop": ("—", "—", "✓", "✓", "—", "—", "✓", "✓"),
    "burn-time owner": ("loop", "loop", "constant", "constant",
                        "loop", "loop", "optimiser", "optimiser"),
    "input file ⁺": ("committed", "committed", "committed", "committed",
                     "committed", "committed", "lifted", "lifted"),
    "output-time loop (MDA_Output)": ("n/a", "n/a", "n/a", "n/a",
                                      "upstream", "upstream", "none", "none"),
}


def matrix_cell(arm: Arm, row: str) -> str:
    """The cell *row* of the plan's matrix holds for *arm*, regenerated."""
    tick = {True: "✓", False: "—"}
    if row == "MDA solve":
        return arm.mda
    if row == "stopping rule":
        return arm.stopping_rule
    if row == "block schedule":
        return {"none": "—", "single block": "(one block)", "once": "one pass"}[
            arm.schedule_passes
        ]
    if row == "arrangement · node (build after physics)":
        return tick[arm.arrangement_node]
    if row == "arrangement · method (prime)":
        return tick[arm.arrangement_method]
    if row == "deferral per_call":
        return tick[arm.defer_per_call]
    if row == "deferral per_run":
        return tick[arm.defer_per_run]
    if row == "burn time out of the loop":
        return tick[arm.burn_time_out_of_loop]
    if row == "burn-time owner":
        return arm.burn_time_owner
    if row == "input file ⁺":
        return arm.input_file
    if row == "output-time loop (MDA_Output)":
        return "n/a" if arm.output_loop is None else arm.output_loop
    raise KeyError(f"{row!r} is not a row of the matrix")


def matrix() -> dict[str, tuple[str, ...]]:
    """The whole matrix regenerated from :data:`ARMS`, in the plan's order."""
    return {
        row: tuple(matrix_cell(ARMS[name], row) for name in MATRIX_ORDER)
        for row in PLAN_MATRIX
    }


# --------------------------------------------------------------------------
# the rungs
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Rung:
    """One row of EXPERIMENT_REPORT.md §3.2's rung table.

    ``changes_a`` / ``changes_b`` are the fields the step moves; :func:`rung`
    computes the same thing from the arms, and the self-check compares them.
    A rung whose declared difference does not match its composed environments
    is refused — the plan's promise, made a computation.
    """

    phase_a: tuple[str, str]
    phase_b: tuple[str, str]
    isolates: str
    changes_a: tuple[str, ...]
    changes_b: tuple[str, ...]
    #: Whether the two phases' steps move the same set of fields.  The plan
    #: says of the middle rung that it is "the one rung where the phases
    #: differ in kind", so this is declared, not assumed.
    same_in_both_phases: bool
    role: str
    note: str = ""


RUNGS: tuple[Rung, ...] = (
    Rung(
        phase_a=("AR", "A0"),
        phase_b=("BR", "B0"),
        isolates=(
            "the stopping rule — upstream's objective/constraint test at its "
            "two-pass floor vs the coupling-state test at the shared tolerance"
        ),
        changes_a=("mda",),
        changes_b=("mda",),
        same_in_both_phases=True,
        role=(
            "reported, never accepted on: a comparison at unmatched accuracy "
            "by construction"
        ),
    ),
    Rung(
        phase_a=("A0", "A1"),
        phase_b=("B0", "B1"),
        isolates=(
            "burn-time ownership — the loop vs a constant (Phase A) or the "
            "optimiser (Phase B); the one rung where the phases differ in "
            "kind — and, in Phase B only, the output-time loop "
            "(upstream → none), placed on this rung deliberately: it is the "
            "rung already declared to differ in kind between the phases, so "
            "the headline rung B1 → B2 keeps a switch set identical to "
            "A1 → A2"
        ),
        changes_a=("burn_time_owner",),
        changes_b=("burn_time_owner", "output_loop"),
        same_in_both_phases=False,
        role="Phase A: cost and audit at matched map; Phase B: checks 1–3",
        note=(
            "The output-time loop's change sits on this rung and in Phase B "
            "only.  It is the rung already declared to differ in kind between "
            "the phases, so putting it here leaves the headline rung "
            "B1 → B2 with a switch set identical to its Phase A twin "
            "A1 → A2, which is what lets a Phase A ratio be read against "
            "its Phase B twin.  The output-time loop's sweeps are counted per "
            "run and published as their own column, so neither rung's "
            "attribution carries them silently."
        ),
    ),
    Rung(
        phase_a=("A1", "A2"),
        phase_b=("B1", "B2"),
        isolates=(
            "the partitioning intervention — block solves, arrangement at "
            "node and method granularity, and both deferrals"
        ),
        changes_a=(
            "mda",
            "arrangement_node",
            "arrangement_method",
            "defer_per_call",
            "defer_per_run",
        ),
        changes_b=(
            "mda",
            "arrangement_node",
            "arrangement_method",
            "defer_per_call",
            "defer_per_run",
        ),
        same_in_both_phases=True,
        role=(
            "Phase A headline; Phase B headline via B0 → B2, published beside "
            "BR → B2"
        ),
    ),
)


def rung(a: Arm | str, b: Arm | str) -> dict[str, tuple[object, object]]:
    """What changes between two arms, field by field, in the matrix's order.

    Only the matrix's independent rows are compared: the stopping rule, the
    number of schedule passes, whether the burn time is out of the loop and
    which input file is read all follow from those, and reporting them again
    would make a one-thing rung look like four.
    """
    arm_a = ARMS[a] if isinstance(a, str) else a
    arm_b = ARMS[b] if isinstance(b, str) else b
    known = {f.name for f in fields(Arm)}
    missing = [f for f in MATRIX_FIELDS if f not in known]
    if missing:  # pragma: no cover - guards a future field rename
        raise KeyError(f"MATRIX_FIELDS names unknown arm fields {missing}")
    return {
        name: (getattr(arm_a, name), getattr(arm_b, name))
        for name in MATRIX_FIELDS
        if getattr(arm_a, name) != getattr(arm_b, name)
    }


# --------------------------------------------------------------------------
# the three public functions
# --------------------------------------------------------------------------


def env_for(
    arm: Arm | str,
    config: Config,
    *,
    seed: int | None = None,
    pin_hex: str | None = None,
    predicate_mode: str = "frozen",
    campaign: Campaign | None = None,
    pending_ok: bool = False,
    test_set: str | None = None,
    tau: float | None = None,
) -> dict[str, str]:
    """The environment one arm runs under on one configuration, from nothing.

    Every known variable is cleared first and then only what the arm declares
    is set, so an inherited value can never change what is measured.  The
    reference arms compose to an environment with every switch cleared: that
    *is* the arm.

    A switch no tree implements yet is a refusal, not an omission — composing
    the environment without it would run a different arm under this arm's
    name.  ``pending_ok=True`` returns the partial environment for inspection
    and is never used on a run path.
    """
    arm = ARMS[arm] if isinstance(arm, str) else arm
    campaign = campaign or default_campaign()
    if arm.name in config.skips:
        raise SwitchError(
            f"{arm.name} is not active on {config.name}: "
            f"{config.skips[arm.name]}"
        )
    env = switches.base_environment(campaign.tree, runs_dir=campaign.runs_dir)
    terms = arm.terms(
        config,
        pin_hex=pin_hex,
        predicate_mode=predicate_mode,
        campaign=campaign,
        seed=seed,
        test_set=test_set,
        tau=tau,
    )
    pending = switches.unimplemented(terms)
    if pending and not pending_ok:
        raise SwitchError(
            f"{arm.name} on {config.name} asks for "
            + "; ".join(
                f"{t} (needs "
                f"{switches.REGISTRY[t].pending_change or 'a driver change'})"
                for t in pending
            )
            + " — refused rather than composed without it"
        )
    for term, value in terms.items():
        name = switches.REGISTRY[term].driver_name
        if name is None:
            continue
        env[name] = value
    switches.assert_no_retired(env)
    return env


def input_file_for(
    arm: Arm | str, config: Config, *, campaign: Campaign | None = None
) -> Path:
    """The input file this arm reads on this configuration.

    The configuration's committed input file, except where the optimiser owns
    the burn time: that arm reads the lifted input file, a derived copy
    differing in exactly three lines and produced by a committed stage.  The
    committed input files are never edited (D9).
    """
    arm = ARMS[arm] if isinstance(arm, str) else arm
    campaign = campaign or default_campaign()
    if arm.input_file == "lifted" and config.pulsed:
        return (
            campaign.derived_input_dir / config.name / f"{config.name}_lifted.IN.DAT"
        )
    return config.input_path


def active_arms(config: Config, phase: str | None = None) -> tuple[str, ...]:
    """Arms this configuration runs, with the skipped ones left out by name.

    A skip is recorded, never silent: ``config.skips`` says which arm and why.
    """
    return tuple(
        name
        for name, arm in ARMS.items()
        if name not in config.skips and (phase is None or arm.phase == phase)
    )


def skipped_arms(config: Config) -> Mapping[str, str]:
    """Arms inactive on this configuration, arm -> recorded reason."""
    return config.skips
