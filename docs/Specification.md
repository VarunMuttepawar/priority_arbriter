The arbiter supports:

Multiple concurrent requesters

Programmable class-based priority

A fairness mechanism to avoid indefinite starvation

Downstream backpressure via a ready/valid-style interface

The design is expected to operate correctly under continuous load, intermittent backpressure, and dynamic request patterns.

2.1 Arbitration Behavior
At most one requester shall be granted access in any given cycle.

When multiple requests are asserted, the arbiter shall select one requester based on:

a. Class priority

b. An internal arbitration mechanism for resolving ties

Higher class priority requesters should generally be favored over lower class priority requesters.

2.2 Fairness
The arbiter shall include a mechanism to prevent starvation.

A requester that continues to assert its request should eventually receive a grant.

The fairness mechanism shall be parameterizable via FAIR_K

2.3 Backpressure Handling
The arbiter shall observe the gnt_ready signal from downstream logic.

When gnt_ready is deasserted:

The currently selected grant, if any, shall be held stable.

No new grant shall be issued until backpressure is released.

2.5 Reset Behavior
The arbiter shall support an active-low reset.

Upon reset:

All internal state shall return to a known value

No grants shall be issued unless valid requests are present