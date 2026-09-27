---
type: regex
target: last_message
match: contains
flags: i
weight: 0.5
---
A\.conj\(\)\.T\s*@\s*y|A\.T\.conj\(\)|np\.conj\(self\.A\)\.T|y\.conj\(\)\s*@\s*self\.A|MatrixMult
