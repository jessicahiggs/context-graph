# eval-harness

Runs a fixed suite against each agent build and reports scores.

It reports [[acceptance-rate]] and [[hallucination-rate]]. Both are published to the
platform dashboard; neither is computed anywhere else.

It evaluates [[coding-agent]]. It does not read from [[context-layer]] — the harness
is deliberately isolated so a context regression cannot mask itself in the scores.

Owner: platform team.
