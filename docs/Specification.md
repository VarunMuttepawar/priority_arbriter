# Priority Arbiter Specification

## Module Interface

```systemverilog
module priority_arbiter #(
    parameter int N          = 4,
    parameter int PRIO_WIDTH = 4
)(
    input  logic               clk,
    input  logic               reset,      // Active-LOW
    input  logic [N-1:0]       req,
    output logic [N-1:0]       gnt,
    output logic               gnt_valid
);
```

## Parameters

- `N`: Number of requesters (default: 4)
- `PRIO_WIDTH`: Width of priority values (default: 4)

## Ports

### Inputs
- `clk`: Clock signal (rising edge triggered)
- `reset`: Active-LOW reset signal
- `req[N-1:0]`: Request signals from N requesters (one-hot encoded possible)

### Outputs
- `gnt[N-1:0]`: Grant signals (one-hot encoded, only one bit high at a time)
- `gnt_valid`: Indicates when a grant is valid

## Functional Requirements

### Base Priority
Each requester has a static base priority:
- `base_prio[i] = N - 1 - i`
- Requester 0 has highest base priority
- Requester N-1 has lowest base priority

### Effective Priority with Aging
The arbiter maintains an effective priority for each requester:
1. **Initial State**: Effective priority = base priority
2. **Continuous Request Aging**: If a requester continuously asserts `req[i]` for consecutive cycles without being granted, its effective priority increments by 1 per cycle (up to saturation)
3. **Grant Reset**: When granted, effective priority resets to base priority
4. **Request Drop**: If a request is dropped (deasserted), the effective priority holds (no aging)
5. **Saturation**: Effective priority saturates at MAX_PRIO = 2^PRIO_WIDTH - 1 (no wrap-around)

### Arbitration Logic
On each cycle:
1. Among all active requesters (`req[i] == 1`), select the one with highest effective priority
2. On tie, select the lowest index
3. Assert `gnt[winner]` and `gnt_valid = 1`
4. If no requests, `gnt = 0` and `gnt_valid = 0`

### Key Behaviors
- **Anti-Starvation**: Continuous aging ensures low-priority requesters eventually win
- **No First-Cycle Aging**: A requester's first request cycle does not age
- **Priority Reset on Grant**: Prevents immediate re-wins by recently granted requesters
- **Hold on Drop**: Dropped requests don't age, but retain their current priority

## Reset Behavior
On `reset == 0` (active-LOW):
- All effective priorities reset to base priorities
- `req_d` (previous request) resets to 0
- Grants are deasserted

## Example Scenario

Initial state (after reset):
```
eff_prio[0] = 3, eff_prio[1] = 2, eff_prio[2] = 1, eff_prio[3] = 0
```

Cycle 1: `req = 0b1001` (req[3] and req[0])
- Winner: req[0] (higher priority)
- `gnt = 0b0001`, `eff_prio[0] → 3` (reset)

Cycle 2-7: `req = 0b1001` (continuous)
- req[3] ages: 0→1→2→3→4→...
- Winner alternates as req[3] overtakes req[0]

This demonstrates anti-starvation through aging.

