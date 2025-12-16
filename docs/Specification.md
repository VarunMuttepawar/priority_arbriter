Design a priority arbiter for N requesters that combines fixed priority with aging-based fairness.
The arbiter must ensure forward progress while preserving priority ordering whenever possible.

Each requester has:
A base priority and an effective priority which increases over time with aging.

The arbiter uses the dynamic priority to select grants.

Lower indices correspond to higher base priority.

Requesters that are not granted will increase their effcective priority over time.

Aging is related to how long a requester has been waiting

At most one grant may be asserted per cycle

Grants are issued only to active requesters

When multiple requesters compete, priority should influence selection

The mechanism should prevent starvation

Requesters that continuously request service should eventually be granted


