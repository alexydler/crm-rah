---
name: graphify-local
description: Use for cross-file dependencies, callers, impact and code paths in this CRM when a structural graph helps. Local AST only; use direct search for a known symbol or simple lookup.
compatibility: macOS sandbox-exec and the locally audited graphifyy 0.9.20 CLI; no MCP, network or model backend.
---

# Local Code Navigation

1. Use Grep/Glob for a known file, endpoint or symbol. Do not build a graph for a simple lookup.
2. For relationships across files, use `sh .opencode/bin/graphify-local query "symbols"`. The output budget is 1500 tokens, not a model invocation.
3. Use the wrapper's `explain`, `path` or `affected` with precise node names from a query. Cite source locations and distinguish extracted from inferred edges.
4. If the graph is absent or source has changed, `sh .opencode/bin/graphify-local build` rebuilds AST with local normalization/clustering, not semantic extraction or LLM labeling. It writes generated files; never modifies CRM source. Full rebuild avoids the partial incremental raw-graph behavior of 0.9.20.
5. The wrapper removes inherited credentials and denies all network through macOS sandbox-exec. Do not bypass it, add flags, run generic `/graphify`, install plugins/hooks or invoke semantic extraction, labeling, cloud or live databases.
6. Ask the user before any LLM analysis, paid operation or external API. A graph is navigation evidence, not proof of authorization or tenant isolation.
7. Do not save Q&A memories or read the full graph/report as ambient context. Query/path/explain may update a local cache timestamp even with query logging disabled.
8. Read only the relevant source window to verify a graph result. JSON/config and dynamic calls may have incomplete edges; no path is not proof of no dependency.

Run `sh .opencode/bin/graphify-local --help` for the supported wrapper commands. See `docs/AI_CONTEXT_POLICY.md` for limits and `docs/SETUP_REPORT.md` for measured results.
