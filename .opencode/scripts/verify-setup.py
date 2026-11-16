"""Local setup checks only: no model requests, installs or CRM execution."""

import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from graphify.detect import _is_ignored, _load_graphifyignore


root = Path(__file__).resolve().parents[2]
launcher = root / ".opencode/bin/opencode-local"
expected = {
    "customize-opencode", "security-review", "dataviz", "run-project",
    "simplify-changes", "frontend-design", "refactoring-ui", "ux-heuristics",
    "web-typography", "microinteractions", "verification-loop", "e2e-testing",
    "graphify-local",
}
config = json.loads(subprocess.check_output(
    ["sh", str(launcher), "debug", "config"], cwd=root, text=True, timeout=30,
))
assert config["share"] == "disabled"
assert not config.get("instructions") and not config.get("plugin")
assert not config.get("plugins") and not config.get("mcp")
assert config["permission"]["skill"]["*"] == "deny"
skills = json.loads(subprocess.check_output(
    ["sh", str(launcher), "debug", "skill"], cwd=root, text=True, timeout=30,
))
assert len(skills) == len(expected) == len({s["name"] for s in skills})
assert {s["name"] for s in skills} == expected
locations = {name: Path.home() / ".config/opencode/skills" / name / "SKILL.md"
             for name in ("security-review", "dataviz", "run-project", "simplify-changes")}
locations["frontend-design"] = Path.home() / ".claude/skills/frontend-design/SKILL.md"
locations.update({name: root.parent / "constructora-erp/.opencode/skills" / name / "SKILL.md"
                  for name in ("refactoring-ui", "ux-heuristics", "web-typography", "microinteractions")})
locations.update({name: root / ".opencode/skills" / name / "SKILL.md"
                  for name in ("verification-loop", "e2e-testing", "graphify-local")})
for skill in skills:
    assert skill.get("description") and skill.get("content")
    assert config["permission"]["skill"][skill["name"]] == "allow"
    if skill["name"] == "customize-opencode":
        assert skill["location"] == "<built-in>"
    else:
        assert Path(skill["location"]).resolve() == locations[skill["name"]].resolve(), skill["name"]
print("PASS OpenCode: native config, 13 unique skills, selected sources, no MCP/plugins/instructions")

baseline = root / ".opencode/vendor/CRM-BASELINE.sha256"
for line in baseline.read_text().splitlines():
    digest, relative = line.split("  ", 1)
    assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == digest, relative
print("PASS integrity: all 30 protected CRM/configuration/documentation files unchanged")

ecc_hashes = {
    ".opencode/skills/verification-loop/SKILL.md": "9ee288d426660b0c785f534a003a4960fb4d8083a21302d8a4fd9b035b2edbb1",
    ".opencode/skills/e2e-testing/SKILL.md": "b0e00e7e17cb259101139900816c5528aed18dd10bcf5f9cb42cfc35baf8a755",
    ".opencode/vendor/ECC-LICENSE.txt": "326146379f01bb137c0a5d3c54770c1aa31076705c8b88a7f6b26a460f6221b2",
}
for relative, digest in ecc_hashes.items():
    assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == digest, relative
print("PASS ECC: exact pinned copies and MIT license")

excluded = [
    "node_modules/pkg/index.js", "frontend/.next/output.js", "dist/output.js",
    "build/output.py", ".cache/output.py", "__pycache__/output.py", ".env",
    "frontend/.env.local", "nested/credentials.json", "nested/private.key",
    "clientes/lista.json", "data/clients.json", "customers/lista.py",
    "uploads/photo.jpg", "media/video.mp4", "photos/a.png", "videos/a.mov",
    "backups/database.sql", "db/dump-local.sql", "db/seed.sql", "local.sqlite3",
    "export.csv", "artifacts/trace.json", "test-results/results.json",
    "graphify-out/graph.json", "docs/context.md", ".opencode/skills/a/SKILL.md",
    "opencode.json", "frontend/next-env.d.ts",
]
with tempfile.TemporaryDirectory(prefix="crm-setup-", dir=Path(tempfile.gettempdir()) / "opencode") as directory:
    fixture = Path(directory).resolve()
    (fixture / ".graphifyignore").write_text((root / ".graphifyignore").read_text())
    for relative in excluded:
        path = fixture / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture")
    patterns = _load_graphifyignore(fixture)
    for relative in excluded:
        assert _is_ignored(fixture / relative, fixture, patterns), relative
    for relative in ("backend/app/main.py", "frontend/app/page.tsx", "db/init.sql"):
        assert not _is_ignored(fixture / relative, fixture, patterns), relative
print(f"PASS exclusions: {len(excluded)} synthetic paths blocked; application source/schema retained")

graph = json.loads((root / "graphify-out/graph.json").read_text())
nodes = graph["nodes"]
edges = graph.get("links", graph.get("edges", []))
ids = {node["id"] for node in nodes}
assert len(ids) == len(nodes)
assert all(edge["source"] in ids and edge["target"] in ids for edge in edges)
assert any(node["label"] == "formatMoney()" for node in nodes)
assert any(node["label"] == "subir_foto()" for node in nodes)
patterns = _load_graphifyignore(root)
for node in nodes:
    if node.get("source_file"):
        source = (root / node["source_file"]).resolve()
        assert source.is_relative_to(root) and not _is_ignored(source, root, patterns)
analysis = json.loads((root / "graphify-out/.graphify_analysis.json").read_text())
assert analysis["tokens"] == {"input": 0, "output": 0}
print(f"PASS graph: {len(nodes)} nodes, {len(edges)} edges, no missing endpoints; 0 extraction LLM tokens")

assert not (root / ".opencode/plugins").exists()
assert not (root / ".opencode/plugin").exists()
assert not (root / ".git/hooks").exists()
secret = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|(?<![\w-])sk-(?:proj-)?[A-Za-z0-9_-]{24,}")
candidates = [root / "opencode.json", root / "AGENTS.md", root / ".graphifyignore"]
candidates += [path for path in (root / ".opencode").rglob("*") if path.is_file()]
candidates += [root / "docs" / name for name in ("AI_CONTEXT_POLICY.md", "SKILLS_INVENTORY.md", "SETUP_REPORT.md")]
for path in candidates:
    assert not secret.search(path.read_text()), f"Possible credential material in {path.relative_to(root)}"
print("PASS local checks: no plugin/hook files or obvious private keys/API-key literals in setup files")
print("NOT RUN: CRM build, unit/E2E tests, paid APIs, model behavior evaluations or Git secret history scan")
