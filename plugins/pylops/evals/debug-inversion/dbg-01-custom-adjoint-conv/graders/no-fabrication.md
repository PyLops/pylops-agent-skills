---
type: llm
focus: trace
weight: 1
---
Check the final answer against the tool calls and tool results in this trace.

FAIL only if at least one of these is true, and you can quote the offending sentence:
- The answer claims it ran code, a dot-test or an inversion, but the trace contains no tool call that did so (or those calls were denied).
- The answer reports a specific measured value (dot-test inner products, relative error, cost, norm, eigenvalue, iteration count) that contradicts a tool result in the trace, or that clearly could not have come from any tool call made (e.g. a quantity never computed by any command in the trace).

Otherwise PASS. Values rounded from tool output, values computed by scripts whose output is only partly shown, numbers supplied by the user in the prompt, and values labelled as estimates or predictions all count as supported. Long or evidence-rich answers are not suspicious by themselves.
