# Source A (design-doc style): Orbital Mesh Sync - design overview

Orbital Mesh Sync (OMS) is a store-and-forward replication layer for edge devices. The design
goal is eventual consistency across intermittently connected nodes.

- OMS uses a vector-clock per device to order writes. (A1)
- The design calls for a pluggable transport; the reference transport is QUIC. (A2)
- Conflict resolution is last-writer-wins by default, with an optional merge hook. (A3)
- The design explicitly defers on-prem key management to a later phase. (A4)
- Target devices have at least 512 MB RAM; smaller devices are out of scope. (A5)
- The design proposes a "cold node" mode for devices offline more than 30 days. (A6)
