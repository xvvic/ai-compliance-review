"""Resolve the installed runtime dependency closure into an exact lock file."""
import importlib.metadata as metadata
from pathlib import Path
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
pending = [Requirement(line).name for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
resolved = {}
while pending:
    name = canonicalize_name(pending.pop())
    if name in resolved:
        continue
    distribution = metadata.distribution(name)
    resolved[name] = distribution.version
    for spec in distribution.requires or []:
        requirement = Requirement(spec)
        if requirement.marker is None or requirement.marker.evaluate({"extra": ""}):
            pending.append(requirement.name)
(ROOT / "requirements.lock").write_text("# Windows x64 / Python 3.13 runtime dependencies\n" + "\n".join(f"{name}=={version}" for name, version in sorted(resolved.items())) + "\n", encoding="utf-8")
