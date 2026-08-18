# acceptance-rate

Share of agent-proposed changes a human approves without editing.

Reported by [[eval-harness]]. Used as the release gate for [[coding-agent]] — a build
ships only if acceptance rate holds above the previous release.

Deliberately preferred over raw output volume, which rewards an agent for producing
more work rather than better work.
