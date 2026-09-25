"""Check that every collected project test names declared requirement IDs."""
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(r"REQ-(?:USR|EVT|REG)-(?:B)?\d{2}\b")
GROUPS = ("user-service", "event-service", "registration-service", "integration")


class TraceabilityAudit:
    def __init__(self, group):
        self.group = group
        names = GROUPS[:3] if group == "integration" else (group,)
        self.declared = set()
        for name in names:
            self.declared.update(PATTERN.findall(
                (ROOT / ".kiro/specs" / name / "requirements.md").read_text()
            ))
        self.items = []
        self.invalid = []

    def pytest_collection_finish(self, session):
        for item in session.items:
            references = set(PATTERN.findall(item.name + " " + (item.obj.__doc__ or "")))
            for marker in item.iter_markers("req"):
                references.update(str(argument) for argument in marker.args)
            unknown = references - self.declared
            if not references or unknown:
                self.invalid.append({"test": item.nodeid, "unknown": sorted(unknown)})
            self.items.append({"test": item.nodeid, "requirements": sorted(references)})
        destination = ROOT / ".checks" / f"traceability-{self.group}.json"
        destination.parent.mkdir(exist_ok=True)
        destination.write_text(json.dumps(self.items, indent=2) + "\n")


def run_group(group):
    import os
    import pytest

    directory = ROOT if group == "integration" else ROOT / "services" / group
    os.chdir(directory)
    sys.path.insert(0, str(directory))
    audit = TraceabilityAudit(group)
    target = "tests/service_integration" if group == "integration" else "tests"
    result = pytest.main(["-c", str(ROOT / "pyproject.toml"), target, "--collect-only", "-q"], plugins=[audit])
    print(f"TRACEABILITY {group}: {len(audit.items)} cases, {len(audit.invalid)} invalid")
    for problem in audit.invalid[:20]:
        print(json.dumps(problem))
    return int(result) or (1 if audit.invalid else 0)


def main():
    if len(sys.argv) == 2 and sys.argv[1] in GROUPS:
        return run_group(sys.argv[1])
    if len(sys.argv) != 1:
        raise SystemExit("Usage: check_traceability.py [user-service|event-service|registration-service|integration]")
    failed = False
    for group in GROUPS:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), group],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        log = ROOT / ".checks" / f"traceability-{group}.log"
        log.parent.mkdir(exist_ok=True)
        log.write_text(result.stdout)
        for line in result.stdout.splitlines():
            if line.startswith("TRACEABILITY") or (result.returncode and line.startswith('{"test"')):
                print(line)
        if result.returncode:
            if "TRACEABILITY" not in result.stdout:
                print(result.stdout)
            failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
