from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Tuple


def extract_revenue_series(rows: List[Dict[str, Any]]) -> List[Tuple[int, float]]:
    series: Dict[int, float] = {}
    for row in rows:
        text = str(row.get("text", ""))
        if "revenue" not in text.lower():
            continue

        year = _extract_year(text) or _extract_year(str(row.get("filename", "")))
        amount = _extract_amount(text)
        if year is None or amount is None:
            continue

        current = series.get(year)
        if current is None or amount > current:
            series[year] = amount

    return sorted(series.items(), key=lambda item: item[0])


def build_revenue_chart(series: List[Tuple[int, float]]) -> Optional[Dict[str, Any]]:
    if len(series) < 2:
        return None

    years = [year for year, _ in series]
    values = [value for _, value in series]

    min_value = min(values)
    max_value = max(values)
    value_range = max(max_value - min_value, 1.0)

    width = 520
    height = 240
    padding = 36

    points: List[Tuple[float, float]] = []
    for idx, (year, value) in enumerate(series):
        x = padding + (idx / max(len(series) - 1, 1)) * (width - 2 * padding)
        y = padding + (1.0 - (value - min_value) / value_range) * (height - 2 * padding)
        points.append((x, y))

    path = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in points)
    circles = "\n".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#1f77b4" />'
        for x, y in points
    )

    svg = "\n".join(
        [
            f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
            f'<rect width="{width}" height="{height}" fill="#ffffff" />',
            f'<path d="{path}" fill="none" stroke="#1f77b4" stroke-width="2" />',
            circles,
            f'<text x="{padding}" y="{height - 12}" font-size="12" fill="#555">{years[0]}</text>',
            f'<text x="{width - padding}" y="{height - 12}" font-size="12" fill="#555" text-anchor="end">{years[-1]}</text>',
            f'<text x="{padding}" y="{padding - 10}" font-size="12" fill="#555">Revenue trend</text>',
            "</svg>",
        ]
    )

    return {
        "type": "line",
        "title": "Revenue trend",
        "x_label": "Year",
        "y_label": "Revenue (USD)",
        "series": [
            {
                "label": "Revenue",
                "points": [{"x": year, "y": value} for year, value in series],
            }
        ],
        "svg": svg,
    }


def _extract_year(text: str) -> Optional[int]:
    match = re.search(r"(19|20)\d{2}", text)
    if match:
        return int(match.group(0))
    return None


def _extract_amount(text: str) -> Optional[float]:
    patterns = [
        r"\$?([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\s?(billion|million|thousand|bn|m|k)",
        r"\$([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)",
    ]
    lowered = text.lower()
    for pattern in patterns:
        match = re.search(pattern, lowered)
        if not match:
            continue
        value = match.group(1).replace(",", "")
        try:
            amount = float(value)
        except ValueError:
            continue
        unit = match.group(2) if len(match.groups()) > 1 else None
        return _scale_amount(amount, unit)

    return None


def _scale_amount(value: float, unit: Optional[str]) -> float:
    if unit is None:
        return value

    unit = unit.lower()
    if unit in {"billion", "bn", "b"}:
        return value * 1_000_000_000
    if unit in {"million", "m"}:
        return value * 1_000_000
    if unit in {"thousand", "k"}:
        return value * 1_000
    return value
