# coding-agent

A semi-autonomous agent that proposes code changes and waits for human approval
before applying them.

It reads context from [[context-layer]] rather than relying on model training data,
which is what keeps it useful on code written after the training cutoff.

It is evaluated by [[eval-harness]] nightly. The metric that gates release is
[[acceptance-rate]] — the share of proposed diffs a human approves unmodified.

Migrated to the v2 context format in June 2026.
