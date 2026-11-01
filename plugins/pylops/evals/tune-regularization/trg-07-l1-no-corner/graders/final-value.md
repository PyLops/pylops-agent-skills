---
type: regex
target: trace
match: contains
weight: 0.5
---
EPS_CHOSEN=\s*(?:(?:0?\.(?:2[5-9]\d*|[3-9]\d*)|1(?:\.0*)?)(?![\d.eE])|(?:(?:2\.[5-9]\d*|[3-9](?:\.\d*)?)e-01|1(?:\.0*)?e\+00)(?!\d))
