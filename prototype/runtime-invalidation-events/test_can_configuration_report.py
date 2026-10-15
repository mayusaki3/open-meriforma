"""Suite 36: deterministic, safe-to-share synthetic configuration reports."""
import json
import tempfile
from pathlib import Path
from can_configuration_report import build_report, to_json, to_markdown, main

candidates = [
    dict(name="baseline", period_ms=10, nominal_bps=500_000,
         data_bps=2_000_000, diagnostic_frames=4),
    dict(name="fast", period_ms=10, nominal_bps=1_000_000,
         data_bps=4_000_000, diagnostic_frames=4),
    dict(name="slow", period_ms=10, nominal_bps=250_000,
         data_bps=1_000_000, diagnostic_frames=16),
]
report = build_report(candidates, max_units=12, cycles=10)
assert report["preferred"] == "fast"
assert [c["name"] for c in report["candidates"]][0] == "fast"
assert all(c["screening_status"] in ("pass", "no_feasible_units")
           for c in report["candidates"])
assert all(c["max_passing_units"] <= 12 for c in report["candidates"])
print("PASS ranked report includes screening status and modeled capacity")

encoded = to_json(report)
assert json.loads(encoded) == report
assert encoded == to_json(build_report(candidates, max_units=12, cycles=10))
assert report["model_only"] and not report["hardware_timing_verified"]
assert not report["physical_safety_verified"]
print("PASS stable JSON roundtrip and explicit unverified flags")

markdown = to_markdown(report)
assert "| Candidate |" in markdown
assert "baseline" in markdown and "fast" in markdown
assert "Limitations" in markdown and "not physical arbitration" in markdown
assert "70.0%" in markdown
print("PASS Markdown comparison table and limitations")

none = build_report([
    dict(name="impossible", period_ms=0.1, nominal_bps=250_000,
         data_bps=1_000_000, diagnostic_frames=30)
], max_units=3, cycles=5)
assert none["preferred"] is None
assert none["candidates"][0]["screening_status"] == "no_feasible_units"
assert none["candidates"][0]["utilization"] is None
assert "None" in to_markdown(none) and "N/A" in to_markdown(none)
print("PASS no-feasible-candidate report avoids fabricated recommendations")

with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    config = root / "candidates.json"
    config.write_text(json.dumps(candidates), encoding="utf-8")
    main(["--candidates", str(config), "--output-dir", str(root / "out"),
          "--max-units", "12", "--cycles", "10"])
    result = json.loads((root / "out" / "can-configuration-report.json").read_text(encoding="utf-8"))
    md = (root / "out" / "can-configuration-report.md").read_text(encoding="utf-8")
    assert result == report and md == markdown
print("PASS CLI writes matching JSON and Markdown files")
print("PASS all can-configuration-report checks")
