---
type: regex
target: trace
match: contains
weight: 0.5
---
python[^\n"]*invert\.py[\s\S]*SNR_DB=\s*-?\d
