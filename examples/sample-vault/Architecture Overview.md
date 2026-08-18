# Architecture Overview

The platform has three long-lived services. Everything else is built on top of them.

- [[coding-agent]] handles multi-step code changes with a human approval gate.
- [[eval-harness]] scores model output on a fixed rubric and publishes the results.
- [[context-layer]] is the retrieval tier that grounds agents in current internal state.

The dependency direction matters: agents read from the context layer, and the eval
harness measures agents. Nothing reads from the eval harness except dashboards.

Owner: platform team. Reviewed quarterly.
