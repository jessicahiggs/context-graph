# context-layer

The retrieval tier. Given a task, it returns the slice of internal state an agent
needs, instead of the agent loading whole documents.

[[coding-agent]] reads context from it. It is the reason agents can answer questions
about systems that changed after the model's training cutoff.

Still serves the v1 format for one legacy consumer; the v2 migration completed for
everything else in June 2026.
