import cocotb
from cocotb.triggers import RisingEdge
from cocotb.clock import Clock
import os
from pathlib import Path
import xml.etree.ElementTree as ET

# -----------------------------------------------------------------------------
# Parameters (must match RTL)
# -----------------------------------------------------------------------------
N = 4
FAIR_K = 8

# -----------------------------------------------------------------------------
# Clock / Reset Helpers
# -----------------------------------------------------------------------------

async def setup_dut(dut):
    """Initialize clock and reset DUT"""
    # Start clock
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset sequence
    dut.reset.value = 0
    dut.req.value = 0
    dut.gnt_ready.value = 1
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.reset.value = 1
    await RisingEdge(dut.clk)

def set_class_prio(dut, prios):
    for i, p in enumerate(prios):
        dut.class_prio[i].value = p

# -----------------------------------------------------------------------------
# TEST 1: Starvation under static class priority
# -----------------------------------------------------------------------------

@cocotb.test()
async def test_starvation_prevention_basic(dut):
    """
    High-priority requester never stops requesting.
    Low-priority requester must still be granted within FAIR_K cycles.
    """

    await setup_dut(dut)

    # req[0] highest class, req[3] lowest
    set_class_prio(dut, [3, 2, 1, 0])
    dut.req.value = 0b1001
    dut.gnt_ready.value = 1

    granted_low = False

    for _ in range(FAIR_K + 2):
        await RisingEdge(dut.clk)
        if dut.gnt.value[3]:
            granted_low = True
            break

    assert granted_low, (
        "STARVATION: low-priority requester never granted"
    )

# -----------------------------------------------------------------------------
# TEST 2: Fairness with all requestors active
# -----------------------------------------------------------------------------

@cocotb.test()
async def test_fairness_all_requesting(dut):
    """
    All requestors assert req continuously.
    Lowest class must still get service eventually.
    """

    await setup_dut(dut)

    set_class_prio(dut, [3, 3, 3, 0])
    dut.req.value = 0b1111
    dut.gnt_ready.value = 1

    seen = [0] * N

    for _ in range(FAIR_K * 2):
        await RisingEdge(dut.clk)
        for i in range(N):
            if dut.gnt.value[i]:
                seen[i] += 1

    assert seen[3] > 0, (
        f"STARVATION: requester 3 never granted, seen={seen}"
    )

# -----------------------------------------------------------------------------
# TEST 3: Backpressure safety (grant hold)
# -----------------------------------------------------------------------------

@cocotb.test()
async def test_fairness_under_backpressure(dut):
    """
    gnt_ready toggles.
    Arbiter must NOT lose fairness state.
    """

    await setup_dut(dut)

    set_class_prio(dut, [3, 2, 1, 0])
    dut.req.value = 0b1111

    granted_low = False

    for cycle in range(FAIR_K * 2):
        # stall every other cycle
        dut.gnt_ready.value = 0 if (cycle % 2) else 1
        await RisingEdge(dut.clk)

        if dut.gnt.value[3] and dut.gnt_ready.value:
            granted_low = True
            break

    assert granted_low, (
        "STARVATION during backpressure: fairness state corrupted"
    )

# -----------------------------------------------------------------------------
# TEST 4: Grant stability during stall
# -----------------------------------------------------------------------------

@cocotb.test()
async def test_grant_stability_when_not_ready(dut):
    """
    When gnt_ready=0, grant must not change.
    """

    await setup_dut(dut)

    set_class_prio(dut, [3, 2, 1, 0])
    dut.req.value = 0b1111
    dut.gnt_ready.value = 1

    await RisingEdge(dut.clk)
    held_grant = int(dut.gnt.value)

    # Stall for multiple cycles
    dut.gnt_ready.value = 0
    for _ in range(4):
        await RisingEdge(dut.clk)
        assert int(dut.gnt.value) == held_grant, (
            "Grant changed while gnt_ready=0"
        )

# -----------------------------------------------------------------------------
# TEST 5: Advanced backpressure with request churn (NEW!)
# -----------------------------------------------------------------------------

@cocotb.test()
async def test_backpressure_invariant_fairness(dut):
    """
    Fairness must advance with time, NOT with accepted grants.
    This test breaks almost all AI-generated arbiters.
    Tests request drops + backpressure combined.
    """

    await setup_dut(dut)

    # req[0] high class, req[3] low class
    set_class_prio(dut, [3, 0, 0, 0])

    dut.req.value = 0b1001  # req[0] and req[3]
    dut.gnt_ready.value = 1

    waited_cycles = 0
    granted = False

    for cycle in range(FAIR_K * 3):

        # Adversarial backpressure pattern
        if cycle % 3 == 0:
            dut.gnt_ready.value = 0
        else:
            dut.gnt_ready.value = 1

        await RisingEdge(dut.clk)

        if dut.req.value[3]:
            waited_cycles += 1

        # Drop and reassert request (AI often resets fairness here)
        if cycle == FAIR_K // 2:
            dut.req.value = 0b0001
        if cycle == FAIR_K // 2 + 2:
            dut.req.value = 0b1001

        if dut.gnt.value[3] and dut.gnt_ready.value:
            granted = True
            break

    assert granted, (
        "Golden-only failure: fairness did not survive "
        "backpressure + request churn"
    )

# -----------------------------------------------------------------------------
# JUnit Parsing (HUD requirement)
# -----------------------------------------------------------------------------

def _count_failures_errors(results_xml: Path):
    tree = ET.parse(results_xml)
    root = tree.getroot()
    failures = 0
    errors = 0

    for ts in root.findall(".//testsuite"):
        failures += int(ts.get("failures", 0))
        errors += int(ts.get("errors", 0))

    return failures, errors

# -----------------------------------------------------------------------------
# PYTEST RUNNER (REQUIRED BY HUD)
# -----------------------------------------------------------------------------

def test_advanced_priority_arbiter_hidden_runner():
    from cocotb_tools.runner import get_runner

    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent

    sources = [
        proj_path / "sources" / "advanced_priority_arbiter.sv",
    ]

    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel="advanced_priority_arbiter",
        always=True,
    )

    runner.test(
        hdl_toplevel="advanced_priority_arbiter",
        test_module="test_advanced_priority_arbiter",
        waves=True,
    )
