
# ml_model.py
from typing import Tuple, Dict, List

def predict_mode_with_reason(
    weight: int,
    volume: int,
    distance: int,
    priority: int,
    road_available: int,
    rail_available: int,
    air_available: int,
    water_available: int
) -> Tuple[str, List[str], Dict[str, Dict[str, float]]]:
    """
    Returns (recommended_mode, justification_list, comparison_dict)
    comparison_dict[mode] = {"estimated_cost": ..., "time_hours": ..., "co2_kg": ...}
    """

    # Convert availability flags to booleans
    road = bool(int(road_available))
    rail = bool(int(rail_available))
    air = bool(int(air_available))
    water = bool(int(water_available))

    available = []
    if road: available.append("Road")
    if rail: available.append("Rail")
    if air: available.append("Air")
    if water: available.append("Water")

    if not available:
        return "None", ["No transport mode is available (all availability flags are false)."], {}

    # heuristic constants (tune these later)
    cost_per_km = {"Road": 5.0, "Rail": 3.0, "Air": 10.0, "Water": 2.0}
    avg_speed_kmph = {"Road": 60.0, "Rail": 80.0, "Air": 600.0, "Water": 30.0}
    co2_per_km_per_ton = {"Road": 0.2, "Rail": 0.05, "Air": 0.5, "Water": 0.02}
    # combine weight & volume into a rough ton-equivalent factor
    ton_equivalent = max(0.001, (weight + volume * 0.2) / 1000.0)  # tons

    comparison = {}
    for m in available:
        est_cost = cost_per_km[m] * distance * (ton_equivalent * 100)  # scaled
        time_hours = distance / avg_speed_kmph[m] if avg_speed_kmph[m] > 0 else float("inf")
        co2_kg = co2_per_km_per_ton[m] * distance * ton_equivalent * 1000.0  # kg CO2 total for cargo (approx)
        comparison[m] = {
            "estimated_cost": round(est_cost, 2),
            "time_hours": round(time_hours, 2),
            "co2_kg": round(co2_kg, 2)
        }

    # Scoring: lower is better
    # Normalize roughly by weighting cost, time and emissions
    scores = {}
    for m, v in comparison.items():
        # weight priority effect: higher priority pushes towards faster modes (lower time)
        priority_factor = 1.0
        # assume priority 1 (low) ... 5 (high); scale time penalty:
        if isinstance(priority, (int, float)):
            priority_factor = max(0.5, 1.0 - (priority - 1) * 0.12)  # higher priority -> smaller factor so time matters more

        score = v["estimated_cost"] * 0.6 + (v["time_hours"] * 100.0) * 0.3 * (1.0/priority_factor) + v["co2_kg"] * 0.1
        scores[m] = score

    # If priority is very high and air is available, prefer Air
    if priority >= 4 and "Air" in available:
        recommended = "Air"
    else:
        # choose min score
        recommended = min(scores, key=scores.get)

    # Build justification lines
    reasons = []
    for m, v in comparison.items():
        reasons.append(
            f"{m}: cost ≈ {v['estimated_cost']} units, time ≈ {v['time_hours']} hrs, CO₂ ≈ {v['co2_kg']} kg."
        )

    # Add comparative statement
    reasons.append(
        f"Final choice → {recommended}. Selected because it gives the best weighted trade-off (cost/time/emissions) "
        f"for the provided inputs; priority={priority} and availability={available} considered."
    )

    return recommended, reasons, comparison