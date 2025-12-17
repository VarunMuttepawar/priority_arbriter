# Advanced Priority Arbiter Design Specification

## 1. Overview

Design a high-performance priority arbiter that manages access to a shared resource among multiple requesters. The arbiter must balance competing goals: honoring priority relationships, ensuring fairness to prevent starvation, and correctly handling downstream backpressure.

This arbiter is intended for use in systems where:
- Multiple agents compete for a shared resource (e.g., memory controller, bus, processing unit)
- Some agents have higher priority than others based on their class
- All agents must eventually make forward progress regardless of priority
- The downstream resource may not always be ready to accept new grants

## 2. Interface

### 2.1 Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `N` | int | Number of requesters (default: 4, range: 2-16) |
| `PRIO_WIDTH` | int | Bits per priority level (default: 4) |
| `FAIR_K` | int | Fairness threshold parameter (default: 15) |

### 2.2 Ports

#### Clock and Reset
- `clk` (input): System clock, all state transitions occur on rising edge
- `reset` (input): Active-low asynchronous reset

#### Request Interface
- `req[N-1:0]` (input): Request vector, one bit per requester
  - `req[i] = 1`: Requester `i` is requesting access
  - `req[i] = 0`: Requester `i` is idle
  - Requests may assert/deassert at any time
  - Multiple requests may be asserted simultaneously

- `class_prio[N-1:0][PRIO_WIDTH-1:0]` (input): Priority value per requester
  - Higher numeric value = higher priority
  - Programmable per requester, may change dynamically
  - Valid range: 0 to (2^PRIO_WIDTH - 1)

#### Grant Interface
- `gnt[N-1:0]` (output): Grant vector, one-hot encoded
  - At most one bit may be asserted per cycle
  - `gnt[i] = 1`: Requester `i` is granted access
  - All other bits must be 0 when `gnt[i] = 1`

- `gnt_valid` (output): Indicates a valid grant is present
  - `gnt_valid = 1`: One bit in `gnt[]` is asserted
  - `gnt_valid = 0`: No grant is active (`gnt[] = 0`)

#### Backpressure Interface
- `gnt_ready` (input): Downstream ready signal
  - `gnt_ready = 1`: Downstream can accept the current grant
  - `gnt_ready = 0`: Downstream cannot accept, grant must be held

## 3. Functional Requirements

### 3.1 Basic Arbitration Rules

**R1: One-Hot Grant Encoding**
- The `gnt[]` vector shall be one-hot encoded (at most one bit set)
- When `gnt_valid = 1`, exactly one bit in `gnt[]` shall be asserted
- When `gnt_valid = 0`, all bits in `gnt[]` shall be 0

**R2: Grant Valid Consistency**
- `gnt_valid` shall be 1 if and only if at least one bit in `gnt[]` is 1

**R3: Request Requirement**
- A grant shall only be issued if the corresponding request is active
- If `gnt[i] = 1`, then `req[i]` must be 1 (in the same cycle or held from backpressure)

### 3.2 Class-Based Priority

**R4: Priority Ordering**
- When multiple requests are present, the arbiter shall prefer higher `class_prio` requesters
- If requester A has `class_prio[A] > class_prio[B]`, and both are requesting, requester A should generally be granted first

**R5: Tie Breaking**
- When multiple requesters have identical `class_prio` values, the arbiter shall use a secondary mechanism to select one
- The tie-breaking mechanism shall be deterministic (repeatable for the same conditions)
- The tie-breaking mechanism should contribute to fairness (avoid always selecting the same requester)

### 3.3 Fairness and Starvation Prevention

**R6: Forward Progress Guarantee**
- A requester that continuously asserts its request shall eventually receive a grant
- This guarantee applies even if higher-priority requesters are also continuously requesting
- No requester shall be indefinitely starved

**R7: Fairness Mechanism Behavior**
- The arbiter shall include an internal fairness mechanism that promotes lower-priority requesters over time
- The fairness mechanism shall be parameterized by `FAIR_K`
- Larger `FAIR_K` values result in longer waiting tolerance before fairness intervention
- Smaller `FAIR_K` values result in more aggressive fairness (quicker intervention)

**R8: Fairness Timing Semantics (CRITICAL)**
- The fairness mechanism shall advance based on elapsed time (clock cycles), NOT based on accepted grants
- A requester waiting during backpressure shall continue to age/accumulate fairness credit
- Fairness state shall update every cycle a request is active, regardless of whether downstream is ready

**Rationale:** This prevents a scenario where a low-priority requester waits indefinitely during prolonged backpressure while higher-priority requests continue to hold the grant.

### 3.4 Backpressure Handling

**R9: Grant Hold Behavior**
- When `gnt_ready = 0` (backpressure active), the current grant shall be held stable
- The `gnt[]` and `gnt_valid` outputs shall not change while `gnt_ready = 0`
- The held grant shall remain valid even if the corresponding request deasserts

**R10: Backpressure Release**
- When backpressure is released (`gnt_ready = 1`), the arbiter may issue a new grant in the next cycle
- If the request corresponding to the held grant has deasserted during backpressure, a new grant may be issued immediately upon release

**R11: Continuous Backpressure**
- The arbiter shall correctly handle arbitrarily long backpressure periods (many consecutive cycles with `gnt_ready = 0`)
- Internal fairness state shall continue to evolve correctly during backpressure

**R12: No New Grants During Backpressure**
- While `gnt_ready = 0`, the arbiter shall not issue new grants
- Only the existing grant may be held; no grant transitions are permitted

### 3.5 Reset Behavior

**R13: Reset Assertion**
- The `reset` signal is active-low (0 = reset active, 1 = normal operation)
- Reset may be asserted asynchronously at any time
- All internal state shall be reset to known initial values

**R14: Reset Release**
- Upon reset deassertion, the arbiter shall begin normal operation on the next clock edge
- If requests are present after reset, the arbiter may issue a grant based on priority

**R15: Post-Reset Grants**
- Immediately following reset (on the first cycle after reset release), grants may or may not be issued depending on request state
- No spurious grants shall occur during reset

## 4. Behavioral Scenarios

### 4.1 Single Requester
- If only one requester is active, it shall be granted (subject to backpressure)
- Priority and fairness mechanisms are not relevant

### 4.2 Multiple Requesters, Distinct Priorities
- The highest-priority requester shall typically receive the grant
- Lower-priority requesters shall eventually be granted due to fairness mechanism

### 4.3 Multiple Requesters, Same Priority
- Tie-breaking mechanism shall select one requester
- Selection should vary over time to ensure fairness

### 4.4 Intermittent Backpressure
- Grants shall be held during backpressure cycles
- New grants shall be issued when backpressure is released

### 4.5 Prolonged Backpressure with Continuous Requests
- Fairness mechanism shall continue to advance
- When backpressure releases, a low-priority requester that has been waiting may receive priority over a high-priority requester due to accumulated fairness

### 4.6 Request Deassertion During Held Grant
- If `gnt[i] = 1` due to held grant, and `req[i]` deasserts during backpressure, the grant shall still be held until backpressure releases
- When backpressure releases, a new grant may be issued immediately (since the original requester is no longer requesting)

## 5. Performance and Timing

### 5.1 Latency
- Arbitration decision shall be made within one clock cycle
- A new grant may be issued on the cycle immediately following grant acceptance (when `gnt_ready = 1`)

### 5.2 Throughput
- Under continuous request load with no backpressure, a new grant shall be issued every cycle
- Maximum throughput: 1 grant per clock cycle

### 5.3 Fairness Responsiveness
- The fairness mechanism shall activate within `FAIR_K` cycles of continuous waiting
- Exact behavior depends on implementation, but lower-priority requesters shall not wait indefinitely

## 6. Edge Cases and Corner Conditions

### 6.1 All Requests Deassert
- If all `req[]` bits are 0, `gnt_valid` shall be 0 and `gnt[]` shall be all zeros (unless holding a grant during backpressure)

### 6.2 Changing Priorities During Operation
- `class_prio[]` values may change at any time
- The arbiter shall use the current cycle's priority values for arbitration decisions

### 6.3 Simultaneous Request and Deassertion
- A request may assert and deassert in consecutive cycles
- Grants shall be issued only to currently active requests (except when held by backpressure)

### 6.4 Maximum Fairness Threshold
- When a requester reaches the fairness threshold, it shall have maximum or near-maximum effective priority
- This ensures eventual service regardless of configured class priority

### 7.2 Combinational Outputs (Recommended)
- Output signals should stabilize within the clock period
- No multi-cycle arbitration paths

### 7.3 Parameterization
- The design shall support any value of `N` from 2 to 16
- The design shall support any `PRIO_WIDTH` from 1 to 8
- The design shall support any `FAIR_K` from 1 to (2^FAIR_K - 1)

Implementations will be verified against:
1. **Basic functionality**: Correct one-hot encoding, grant-valid consistency
2. **Priority ordering**: Higher priority requesters receive grants first
3. **Fairness**: Low-priority requesters eventually receive grants
4. **Backpressure handling**: Grants held correctly, fairness advances during backpressure

Deliverables

- SystemVerilog module `advanced_priority_arbiter` in `sources/advanced_priority_arbiter.sv`
- Module shall match the interface specification exactly (port names, widths, types)
- Design shall pass all hidden test cases

Hints and Recommendations

- Backpressure handling requires careful state management
- Test your design with prolonged backpressure scenarios

