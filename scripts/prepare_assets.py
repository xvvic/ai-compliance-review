"""Build a public example from the repository's synthetic evaluation fixture."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / "eval" / "sample1_星云智算_risk_report.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    data["report_markdown"] = (ROOT / "eval" / "sample1_星云智算_report_r2.md").read_text(encoding="utf-8")
    data["review_id"] = "example-synthetic-001"
    data["example"] = True
    data["model"] = ""
    data["material"] = {"chars": data["material"]["chars"]}
    output = ROOT / "assets"
    output.mkdir(exist_ok=True)
    (output / "example-report.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
