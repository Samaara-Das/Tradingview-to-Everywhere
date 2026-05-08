"""Unit tests for the reversed-strategy snapshot swap logic.

Spec: `.claude/spec-reversed-strategy-snapshots.md` (Goal 1).

The swap is a 2-line transform applied in
`SnapshotWorker._set_trade_drawer()` before the four input values are typed
into the Trade Drawer V2 indicator. Tests here cover the math of that
transform in isolation — no browser required.

If Sammy's pending Pine Script update handles reversal at the indicator
level, set `REVERSED_STRATEGY_SNAPSHOTS=false` (env or
`snapshot.reversed_strategy: false` in YAML) and these tests still pass —
they cover both branches.
"""

from __future__ import annotations


def _swap_values(setup: dict, reversed_flag: bool) -> tuple[str, str, str, str]:
    """Pure replica of the transform at `tte/snapshot_worker.py:_set_trade_drawer`.

    Mirrors the live code; if the live code changes, this helper must move
    in lockstep so the tests stay meaningful.
    """
    alert_ts = setup.get("alertTimestamp", "")
    sl_value = setup.get("stopLoss", "")
    tp_value = setup.get("takeProfit", "")
    if reversed_flag:
        sl_value, tp_value = tp_value, sl_value
    return (
        str(alert_ts),
        str(setup.get("entryPrice", "")),
        str(sl_value),
        str(tp_value),
    )


SAMPLE_LONG_SETUP = {
    "alertTimestamp": 1736000000000,
    "entryPrice": 100.0,
    "stopLoss": 99.0,  # original-strategy SL — 1 below entry (risk = 1)
    "takeProfit": 102.0,  # original-strategy TP — 2 above entry (reward = 2)
    # Original R:R = 1:2
}


class TestSwapOff:
    """Flag OFF → original-strategy visual (face-value inputs)."""

    def test_sl_input_gets_stop_loss(self):
        _, _, sl_input, _ = _swap_values(SAMPLE_LONG_SETUP, reversed_flag=False)
        assert sl_input == "99.0"

    def test_tp_input_gets_take_profit(self):
        _, _, _, tp_input = _swap_values(SAMPLE_LONG_SETUP, reversed_flag=False)
        assert tp_input == "102.0"

    def test_entry_and_timestamp_unchanged(self):
        ts, entry, _, _ = _swap_values(SAMPLE_LONG_SETUP, reversed_flag=False)
        assert ts == "1736000000000"
        assert entry == "100.0"


class TestSwapOn:
    """Flag ON → reversed-strategy visual (Coda i-BqLTT9VWoP)."""

    def test_sl_input_receives_take_profit(self):
        """Visual SL line should be drawn at the original TP price (102)."""
        _, _, sl_input, _ = _swap_values(SAMPLE_LONG_SETUP, reversed_flag=True)
        assert sl_input == "102.0"

    def test_tp_input_receives_stop_loss(self):
        """Visual TP line should be drawn at the original SL price (99)."""
        _, _, _, tp_input = _swap_values(SAMPLE_LONG_SETUP, reversed_flag=True)
        assert tp_input == "99.0"

    def test_entry_unchanged(self):
        """Entry line stays at the original entry price regardless of flag."""
        _, entry, _, _ = _swap_values(SAMPLE_LONG_SETUP, reversed_flag=True)
        assert entry == "100.0"

    def test_resulting_visual_rr_is_2_to_1(self):
        """Manager Q1 (2026-05-08): R:R 2:1 in the reversed (SHORT) direction."""
        _, entry_s, sl_s, tp_s = _swap_values(SAMPLE_LONG_SETUP, reversed_flag=True)
        entry_p = float(entry_s)
        # Visual SL line is drawn ABOVE entry (where original TP was)
        visual_sl = float(sl_s)
        # Visual TP line is drawn BELOW entry (where original SL was)
        visual_tp = float(tp_s)
        risk = abs(visual_sl - entry_p)  # = 2.0
        reward = abs(entry_p - visual_tp)  # = 1.0
        assert risk == 2.0
        assert reward == 1.0
        assert risk / reward == 2.0  # R:R 2:1


class TestEdgeCases:
    def test_missing_fields_become_empty_strings_not_crash(self):
        """A doc missing stopLoss/takeProfit should not raise."""
        ts, entry, sl, tp = _swap_values({}, reversed_flag=True)
        assert ts == ""
        assert entry == ""
        assert sl == ""
        assert tp == ""

    def test_swap_is_self_inverse(self):
        """Applying the swap twice returns the original."""
        once = _swap_values(SAMPLE_LONG_SETUP, reversed_flag=True)
        # Reconstruct a setup from the swapped result and swap again
        twice_setup = {
            "alertTimestamp": once[0],
            "entryPrice": once[1],
            "stopLoss": once[2],
            "takeProfit": once[3],
        }
        twice = _swap_values(twice_setup, reversed_flag=True)
        # Compare to the unswapped original
        original = _swap_values(SAMPLE_LONG_SETUP, reversed_flag=False)
        assert twice == original
