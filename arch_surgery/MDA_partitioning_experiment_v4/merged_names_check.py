"""The merged same-name functions against the bodies they replaced, evaluated.

The simplification survey (item A8) found three pairs of functions that shared a
name and not a meaning, or a meaning and not a body: ``chain._pin_for`` and
``gate_prime._pin_for`` (the second a strict subset of the first),
``pool.input_file_for`` and ``arms.input_file_for`` (the first the second plus
an assertion), and the two ``cheapest_configuration``s (measured cost against
declared size — renamed, not merged, so nothing to compare).  The merges keep
one implementation each: ``reproduction.entry_pin`` and
``pool.assert_input_file_for`` built on ``arms.input_file_for``.

This script is the evidence that every caller's behaviour is unchanged: the
replaced bodies are transcribed below **verbatim from commit 34c5c3e4** and
evaluated beside the merged ones over every (arm, configuration) pair of the
campaign, every reference burn-time hex the run records on disk carry (or one
fixed hex when there are none), and a grid of seeds and displacements.  It
prints the denominators and exits non-zero on the first disagreement.  No
PROCESS run; the assertion half of ``assert_input_file_for`` (a lifted file
present with the recorded digest) is ``input_files.assert_lifted``'s and is
not exercised here — it is exercised by gate ``artifacts_derive_inputs``.

Usage::

    python merged_names_check.py
"""

from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from harness.core import pool as pool_mod  # noqa: E402
from harness.core.config import default_campaign  # noqa: E402
from harness.experiment import arms as arms_mod  # noqa: E402
from harness.experiment import input_files as input_files_mod  # noqa: E402
from harness.gates import reproduction as reproduction_mod  # noqa: E402


# --- the replaced bodies, verbatim from 34c5c3e4 ---------------------------


def _old_pool_input_file_for(job, campaign):
    """``harness/core/pool.py:340`` at 34c5c3e4, minus the assertion call."""
    arm = arms_mod.ARMS[job.arm]
    if arm.input_file == "lifted" and job.config.pulsed:
        return input_files_mod.lifted_path(job.config, campaign), "lifted"
    return job.config.input_path, "committed"


def _old_gate_prime_pin_for(config, arm, reference):
    """``harness/gates/gate_prime.py:171`` at 34c5c3e4."""
    if not config.pulsed:
        return None
    if arms_mod.ARMS[arm].burn_time_owner != "constant":
        return None
    return reference["t_plant_pulse_burn_hex"]


def _old_chain_pin_for(config, arm, reference, *, seed, delta):
    """``harness/chain.py:520`` at 34c5c3e4."""
    if not config.pulsed:
        return None
    if arms_mod.ARMS[arm].burn_time_owner != "constant":
        return None
    reference_hex = reference["t_plant_pulse_burn_hex"]
    if not delta or seed == 0:
        return reference_hex
    return reproduction_mod.pin_for(reference_hex, seed, delta)


# --- the comparison ---------------------------------------------------------


def reference_hexes(campaign) -> list[str]:
    """Every burn-time hex a record on disk carries; one fixed value if none."""
    found: set[str] = set()
    for path in Path(campaign.runs_dir).rglob("metrics.json"):
        try:
            record = json.loads(path.read_text())
        except Exception:  # noqa: BLE001 - an unreadable record is not this check's business
            continue
        value = record.get("t_plant_pulse_burn_hex")
        if isinstance(value, str):
            found.add(value)
    return sorted(found) or ["0x1.34a0000000000p+10"]


def main() -> int:
    campaign = default_campaign()
    hexes = reference_hexes(campaign)
    seeds = (0, 1, 7)
    deltas = (None, 0.0, campaign.delta)
    n_files = n_pins = 0
    for config in campaign.configurations:
        for arm_name, arm in arms_mod.ARMS.items():
            job = pool_mod.Job(
                phase=arm.phase,
                arm=arm_name,
                config=config,
                seed=0,
                outdir=Path("/nonexistent"),
                run_kind="gate",
            )
            new_path = arms_mod.input_file_for(arm_name, config, campaign=campaign)
            new_kind = "lifted" if new_path != config.input_path else "committed"
            old_path, old_kind = _old_pool_input_file_for(job, campaign)
            if (new_path, new_kind) != (old_path, old_kind):
                print(f"DIFFERS input file: {arm_name}/{config.name}: {new_path} vs {old_path}")
                return 1
            n_files += 1
            for hx in hexes:
                reference = {"t_plant_pulse_burn_hex": hx}
                if reproduction_mod.entry_pin(config, arm_name, reference) != _old_gate_prime_pin_for(
                    config, arm_name, reference
                ):
                    print(f"DIFFERS G2 pin: {arm_name}/{config.name} at {hx}")
                    return 1
                n_pins += 1
                for seed, delta in itertools.product(seeds, deltas):
                    new = reproduction_mod.entry_pin(
                        config, arm_name, reference, seed=seed, delta=delta
                    )
                    old = _old_chain_pin_for(config, arm_name, reference, seed=seed, delta=delta)
                    if new != old:
                        print(f"DIFFERS chain pin: {arm_name}/{config.name} seed {seed} delta {delta}")
                        return 1
                    n_pins += 1
    print(
        f"input file: {n_files} (arm, configuration) pairs, path and kind identical; "
        f"pins: {n_pins} evaluations identical over {len(hexes)} reference hex value(s), "
        f"seeds {seeds}, displacements {deltas}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
