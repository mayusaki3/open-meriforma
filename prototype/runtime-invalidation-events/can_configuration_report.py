"""Suite 36: deterministic JSON/Markdown reporting of synthetic CAN-FD reviews."""
import argparse
import json
from pathlib import Path
from can_configuration_review import compare_configurations

SCHEMA_VERSION = 1
LIMITATIONS = (
    "Synthetic CAN-FD airtime model; not physical arbitration or hardware timing proof.",
    "ACK release is assumed halfway through each period, not causally linked to receipt.",
    "No bit stuffing, retransmission overhead, wiring effects, controller capability or cost.",
    "Capacity screening is not motor safety certification or a production recommendation.",
)


def build_report(candidates, *, max_units=62, cycles=30, utilization_limit=0.70):
    review = compare_configurations(candidates, max_units=max_units,
                                    cycles=cycles, utilization_limit=utilization_limit)
    entries = []
    for item in review["ranked"]:
        selected = item["selected"]
        entries.append({
            "name": item["name"],
            "period_ms": item["period_ms"],
            "nominal_bps": item["nominal_bps"],
            "data_bps": item["data_bps"],
            "diagnostic_frames": item["diagnostic_frames"],
            "max_passing_units": item["max_passing_units"],
            "screening_status": "pass" if selected is not None else "no_feasible_units",
            "utilization": selected["utilization"] if selected else None,
            "utilization_headroom": selected["utilization_headroom"] if selected else None,
            "max_wait_ms": selected["max_wait_ms"] if selected else None,
            "deadline_misses": selected["deadline_misses"] if selected else None,
            "first_unit_utilization": item["rows"][0]["utilization"],
            "first_unit_deadline_misses": item["rows"][0]["deadline_misses"],
        })
    # If no candidate passes screening, there is no recommended candidate.
    feasible = [entry for entry in entries if entry["screening_status"] == "pass"]
    return {
        "schema_version": SCHEMA_VERSION,
        "model_only": True,
        "hardware_timing_verified": False,
        "physical_safety_verified": False,
        "evaluation": {"max_units": max_units, "cycles": cycles,
                       "utilization_limit": utilization_limit},
        "preferred": feasible[0]["name"] if feasible else None,
        "selection_basis": review["selection_basis"],
        "candidates": entries,
        "limitations": list(LIMITATIONS),
    }


def to_json(report):
    return json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def _number(value, *, percent=False):
    if value is None:
        return "N/A"
    return f"{value * 100:.2f}%" if percent else f"{value:.3f}"


def to_markdown(report):
    e = report["evaluation"]
    lines = [
        "# CAN-FD configuration screening (synthetic)",
        "",
        f"- Unit search range: 1–{e['max_units']}",
        f"- Simulated cycles: {e['cycles']}",
        f"- Utilization ceiling: {e['utilization_limit'] * 100:.1f}%",
        f"- Preferred screened candidate: {report['preferred'] or 'None'}",
        f"- Ranking: {report['selection_basis']}",
        "",
        "| Candidate | Period (ms) | Nominal/Data (bps) | Diagnostics/cycle | Max units | Status | Utilization | Headroom | Max wait (ms) | Deadline misses |",
        "|---|---:|---:|---:|---:|---|---:|---:|---:|---:|",
    ]
    for c in report["candidates"]:
        if "|" in c["name"] or "\n" in c["name"] or "\r" in c["name"]:
            name = c["name"].replace("|", "\\|").replace("\n", " ").replace("\r", " ")
        else:
            name = c["name"]
        lines.append(
            f"| {name} | {_number(c['period_ms'])} | "
            f"{c['nominal_bps']}/{c['data_bps']} | {c['diagnostic_frames']} | "
            f"{c['max_passing_units']} | {c['screening_status']} | "
            f"{_number(c['utilization'], percent=True)} | "
            f"{_number(c['utilization_headroom'], percent=True)} | "
            f"{_number(c['max_wait_ms'])} | "
            f"{c['deadline_misses'] if c['deadline_misses'] is not None else 'N/A'} |"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    return "\n".join(lines) + "\n"


DEFAULT_CANDIDATES = [
    {"name": "baseline", "period_ms": 10, "nominal_bps": 500_000,
     "data_bps": 2_000_000, "diagnostic_frames": 4},
    {"name": "fast", "period_ms": 10, "nominal_bps": 1_000_000,
     "data_bps": 4_000_000, "diagnostic_frames": 4},
    {"name": "diagnostic-heavy", "period_ms": 10, "nominal_bps": 500_000,
     "data_bps": 2_000_000, "diagnostic_frames": 16},
]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, help="JSON array of candidate objects")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-units", type=int, default=24)
    parser.add_argument("--cycles", type=int, default=30)
    parser.add_argument("--utilization-limit", type=float, default=0.70)
    args = parser.parse_args(argv)
    candidates = (json.loads(args.candidates.read_text(encoding="utf-8"))
                  if args.candidates else DEFAULT_CANDIDATES)
    report = build_report(candidates, max_units=args.max_units, cycles=args.cycles,
                          utilization_limit=args.utilization_limit)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "can-configuration-report.json").write_text(
        to_json(report), encoding="utf-8")
    (args.output_dir / "can-configuration-report.md").write_text(
        to_markdown(report), encoding="utf-8")
    print("Wrote CAN-FD synthetic screening report (JSON and Markdown)")


if __name__ == "__main__":
    main()
