"""Suite 35: comparative CAN-FD configuration review (synthetic only).

Limits are model-derived screening thresholds, NOT certified capacities.
"""
from can_load_sweep import simulate_load


def review_configuration(*, period_ms, nominal_bps, data_bps,
                         diagnostic_frames=0, utilization_limit=0.70,
                         max_units=62, cycles=30, deadline_ms=None):
    if type(max_units) is not int or not 1 <= max_units <= 62:
        raise ValueError("invalid max_units")
    if type(utilization_limit) not in (int, float) or not 0 < utilization_limit <= 1:
        raise ValueError("invalid utilization limit")
    rows = []
    for units in range(1, max_units + 1):
        result = simulate_load(units=units, period_ms=period_ms,
                               diagnostic_frames=diagnostic_frames,
                               nominal_bps=nominal_bps, data_bps=data_bps,
                               cycles=cycles, deadline_ms=deadline_ms)
        # Both conditions required; a low average load does not imply a deadline pass.
        result["screening_pass"] = (result["utilization"] <= utilization_limit
                                    and result["deadline_misses"] == 0)
        result["utilization_headroom"] = utilization_limit - result["utilization"]
        rows.append(result)
    passing = [r for r in rows if r["screening_pass"]]
    max_passing = max((r["units"] for r in passing), default=0)
    selected = rows[max_passing - 1] if max_passing else None
    return {"period_ms": period_ms, "nominal_bps": nominal_bps,
            "data_bps": data_bps, "diagnostic_frames": diagnostic_frames,
            "utilization_limit": utilization_limit,
            "max_passing_units": max_passing,
            "selected": selected, "rows": rows,
            "model_only": True, "hardware_timing_verified": False,
            "physical_safety_verified": False}


def compare_configurations(candidates, *, max_units=62, cycles=30,
                           utilization_limit=0.70):
    if type(candidates) not in (list, tuple) or not candidates:
        raise ValueError("candidates required")
    names = set()
    comparisons = []
    for candidate in candidates:
        if type(candidate) is not dict or set(candidate) != {
                "name", "period_ms", "nominal_bps", "data_bps", "diagnostic_frames"}:
            raise ValueError("invalid candidate")
        name = candidate["name"]
        if type(name) is not str or not name or name in names:
            raise ValueError("duplicate or invalid candidate name")
        names.add(name)
        result = review_configuration(
            period_ms=candidate["period_ms"],
            nominal_bps=candidate["nominal_bps"],
            data_bps=candidate["data_bps"],
            diagnostic_frames=candidate["diagnostic_frames"],
            max_units=max_units, cycles=cycles,
            utilization_limit=utilization_limit)
        result["name"] = name
        comparisons.append(result)
    # Deterministic ordering; higher feasible unit count first, then larger
    # utilization headroom, then lexicographic candidate name.
    def ranking(item):
        selected = item["selected"]
        headroom = selected["utilization_headroom"] if selected else -float("inf")
        return (-item["max_passing_units"], -headroom, item["name"])
    ranked = sorted(comparisons, key=ranking)
    return {"ranked": ranked, "preferred": ranked[0]["name"],
            "selection_basis": "modeled unit capacity then utilization headroom",
            "model_only": True, "hardware_timing_verified": False,
            "physical_safety_verified": False}
