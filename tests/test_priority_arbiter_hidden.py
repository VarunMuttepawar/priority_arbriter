import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
import os
from pathlib import Path

os.environ.setdefault("WAVES", "1")

# -----------------------------------------------------------------------------
# Clock + Reset helpers
# -----------------------------------------------------------------------------

async def generate_clock(dut, period_ns=10):
    clk = Clock(dut.clk, period_ns, unit="ns")
    cocotb.start_soon(clk.start())

async def reset_dut(dut):
    dut.reset.value = 0
    dut.req.value   = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 1
    await RisingEdge(dut.clk)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def onehot_index(val):
    for i in range(len(val)):
        if val[i]:
            return i
    return None

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

@cocotb.test()
async def test_no_aging_on_first_request(dut):
    """
    Effective priority must NOT increment on the first request cycle.
    """
    await generate_clock(dut)
    await reset_dut(dut)

    # Single requester toggles on
    dut.req.value = 0b0010
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    # It may or may not be granted, but no incorrect behavior should happen
    assert int(dut.gnt.value) in (0b0010, 0b0000)

@cocotb.test()
async def test_continuous_request_ages(dut):
    """
    Continuous request must eventually override base priority.
    """
    await generate_clock(dut)
    await reset_dut(dut)

    # req[0] has highest base priority
    # req[3] lowest, but kept high continuously
    dut.req.value = 0b1001  # req[3] + req[0]

    winner_history = []

    for _ in range(12):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ps")

        if int(dut.gnt_valid.value):
            winner_history.append(onehot_index(dut.gnt.value))

    dut._log.info(f"Grant history: {winner_history}")

    # Eventually req[3] must win at least once
    assert 3 in winner_history, "Lower-priority requester starved!"

@cocotb.test()
async def test_grant_resets_priority(dut):
    """
    After a requester is granted, it should not immediately win again
    if a higher base priority requester exists.
    """
    await generate_clock(dut)
    await reset_dut(dut)

    # req[2] continuous, req[0] joins later
    dut.req.value = 0b0100
    for _ in range(6):
        await RisingEdge(dut.clk)

    dut.req.value = 0b0101  # req[2] + req[0]
    await RisingEdge(dut.clk)
    await Timer(1, unit="ps")

    # req[0] should win after req[2] grant resets its priority
    assert int(dut.gnt.value) == 0b0001

@cocotb.test()
async def test_no_aging_if_request_drops(dut):
    """
    Dropping a request must prevent aging.
    """
    await generate_clock(dut)
    await reset_dut(dut)

    # Toggle req[2]
    dut.req.value = 0b0100
    await RisingEdge(dut.clk)
    dut.req.value = 0
    await RisingEdge(dut.clk)

    # Bring it back
    dut.req.value = 0b0100
    await RisingEdge(dut.clk)
    await Timer(1, unit="ps")

    # Should not immediately win over req[0]
    dut.req.value = 0b0101
    await RisingEdge(dut.clk)

    assert int(dut.gnt.value) == 0b0001

@cocotb.test()
async def test_saturation_no_wrap(dut):
    """
    Effective priority must saturate, not wrap.
    """
    await generate_clock(dut)
    await reset_dut(dut)

    # req[3] continuous only
    dut.req.value = 0b1000

    # Let it age beyond reasonable PRIO_WIDTH
    for _ in range(20):
        await RisingEdge(dut.clk)

    # Should still grant req[3], not wrap around
    assert int(dut.gnt.value) == 0b1000

# -----------------------------------------------------------------------------
# Pytest wrapper (HUD REQUIRED)
# -----------------------------------------------------------------------------

def test_priority_arbiter_hidden_runner():
    from cocotb_tools.runner import get_runner
    import os
    from pathlib import Path

    # Simulator (icarus / verilator / questa, etc.)
    sim = os.getenv("SIM", "icarus")

    # Project root (tests/..)
    proj_path = Path(__file__).resolve().parent.parent

    # RTL sources
    sources = [
        proj_path / "sources" / "priority_arbiter.sv"
    ]

    runner = get_runner(sim)

    # Build step
    runner.build(
        sources=sources,
        hdl_toplevel="priority_arbiter",
        always=True,
    )

    # Test step
    runner.test(
        hdl_toplevel="priority_arbiter",
        test_module="test_priority_arbiter_hidden",
        waves=True,
    )

