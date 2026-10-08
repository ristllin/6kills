# Source B (issue-tracker style): Orbital Mesh Sync - open issues

- OMS-12: cold-node mode is implemented but disabled by default pending field testing. (B1)
- OMS-18: QUIC transport ships; a fallback TCP transport is in progress, not released. (B2)
- OMS-23: on-prem key management is still Backlog; blocks the three regulated customers. (B3)
- OMS-27: the merge hook API is unstable and may change before 1.0. (B4)
- OMS-31: vector-clock storage grows unbounded on cold nodes; a compaction job is planned. (B5)
- OMS-34: last-writer-wins drops concurrent edits in a known race; fix targeted for 1.1. (B6)
