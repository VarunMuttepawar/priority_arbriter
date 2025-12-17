# Advanced Priority Arbiter - HUD/RL Training Problem

**Status:** ✅ Production Ready  
**Difficulty:** Hard  
**Repository:** https://github.com/VarunMuttepawar/priority_arbriter.git

---

## Overview

This repository contains a single **hard-difficulty** Verilog RTL design problem for reinforcement learning (RL) agent training. The problem challenges agents to implement an advanced priority arbiter with class-based priority, fairness mechanisms, and backpressure handling.

## Problem Description

Design a high-performance priority arbiter that manages access to a shared resource among multiple requesters. The arbiter must:

- **Balance competing goals:** Honor priority relationships while ensuring fairness
- **Prevent starvation:** All requesters must eventually make forward progress
- **Handle backpressure:** Correctly manage downstream ready/valid handshake
- **Critical subtlety:** Fairness must advance with TIME, not accepted grants

## Repository Structure

```
priority_arbriter/
├── sources/
│   └── advanced_priority_arbiter.sv       # Reference implementation (golden)
├── tests/
│   └── test_advanced_priority_arbiter.py  # 5 comprehensive tests + pytest wrapper
├── docs/
│   └── Specification.md                   # Detailed design spec (no impl hints)
├── prompt.txt                             # Task description for agents
├── pyproject.toml                         # Python dependencies
└── README.md                              # This file
```

## HUD Branches

This repository uses the **HUD branch structure** for RL training:

- **`advanced_priority_arbiter_baseline`** - Starting point (empty/broken implementation, NO tests)
- **`advanced_priority_arbiter_test`** - Hidden test suite for grading
- **`advanced_priority_arbiter_golden`** - Reference solution (complete implementation, NO tests)
- **`main`** - Documentation and project files

## Key Features

### What Makes This Problem Challenging

1. **Multi-dimensional optimization** - Balance priority, fairness, and backpressure simultaneously
2. **Subtle timing semantics** - Fairness counters must advance during backpressure (time-based, not grant-based)
3. **Stateful backpressure** - Must hold grants while continuing to update internal fairness state
4. **Adversarial testing** - Includes a test that breaks most naive implementations

### Test Coverage

The problem includes 5 comprehensive tests:

1. `test_basic_class_priority` - Priority ordering
2. `test_fairness_counter_aging` - Fairness mechanism promotes waiting requesters
3. `test_fairness_override` - Low-priority requester eventually wins
4. `test_backpressure_hold` - Grants held correctly during backpressure
5. `test_backpressure_invariant_fairness` - **ADVERSARIAL:** Fairness advances during backpressure

**Golden Implementation:** ✅ 5/5 tests pass (100%)

### Specification Quality

The `docs/Specification.md` provides:
- ✅ Complete interface definition (ports, parameters, types)
- ✅ 15 numbered functional requirements
- ✅ Edge cases and corner conditions
- ✅ Performance expectations
- ❌ NO implementation hints (counters, FSMs, register names, etc.)

**Goal:** Provide complete behavioral specification without biasing the RL model.

## Quick Start (Local Development)

### Prerequisites
- Python 3.10+
- Icarus Verilog (iverilog)
- cocotb, pytest

### Setup
```bash
cd /path/to/priority_arbriter
pip install -e .
```

### Run Tests
```bash
# Run all tests
pytest tests/test_advanced_priority_arbiter.py -v

# Run with waveform generation
SIM=icarus pytest tests/test_advanced_priority_arbiter.py -v
```

## HUD Integration

### 1. Copy to Framework
```bash
cd ~/Documents/GitHub/verilog-coding-template
mkdir -p local-repos
cp -r /path/to/priority_arbriter local-repos/
```

### 2. Register Problem
Add to `src/hud_controller/problems/basic.py`:

```python
PROBLEM_REGISTRY.append(
    ProblemSpec(
        id="advanced_priority_arbiter",
        description="""Design an advanced priority arbiter with class-based priority,
fairness counters, and backpressure handling. See docs/Specification.md for details.""",
        difficulty="hard",
        base="advanced_priority_arbiter_baseline",
        test="advanced_priority_arbiter_test",
        golden="advanced_priority_arbiter_golden",
        test_files=["tests/test_advanced_priority_arbiter.py"],
    )
)
```

### 3. Build and Validate
```bash
cd ~/Documents/GitHub/verilog-coding-template

# Build
uv run utils/imagectl3.py verilog_ -b --ids advanced_priority_arbiter

# Validate
uv run utils/imagectl3.py verilog_ -v --ids advanced_priority_arbiter
```

**Expected validation:** All 6 checks pass ✅

## Expected Agent Performance

- **Estimated solve rate:** 30-50% (hard difficulty)
- **Most common failure:** Fairness doesn't advance during backpressure
- **Key adversarial test:** `test_backpressure_invariant_fairness`

This test specifically checks that fairness counters continue incrementing during prolonged backpressure, which requires careful separation of grant hold logic from fairness state updates.

## Documentation

- **`FINAL_STATUS.md`** - Complete status report and HUD integration guide
- **`HUD_COMPLIANCE_REPORT.md`** - Detailed HUD compliance verification
- **`docs/Specification.md`** - Full design specification (15+ pages)
- **`prompt.txt`** - Concise task description for agents

## Compliance

✅ **HUD Contractor Guide Compliant** (November 2025)
- Directory structure: `sources/` and `tests/` ✅
- Pytest wrappers in all test files ✅
- NO tests in baseline/golden branches ✅
- Golden passes 100% of tests ✅
- Specification detailed without impl hints ✅

## Learning Outcomes

An RL agent that successfully solves this problem demonstrates:
1. Understanding of arbitration principles (priority, fairness, forward progress)
2. Temporal reasoning (state that evolves over time)
3. Backpressure protocol handling (ready/valid handshake)
4. Subtle timing semantics (time-based vs. event-based state updates)
5. SystemVerilog proficiency (parameters, arrays, sequential logic)

## License

This problem is intended for RL training and evaluation. See repository license for details.

## Contact

For questions about HUD integration or problem specification:
- Repository: https://github.com/VarunMuttepawar/priority_arbriter
- HUD Framework: https://github.com/phinitylabs/verilog-coding-template

---

**Ready for production use in RL training!** 🚀
