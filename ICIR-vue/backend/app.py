from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "backend" / "data"

app = Flask(__name__)
app.json.ensure_ascii = False

CHART_REGISTRY: dict[str, dict[str, Any]] = {
    "industry": {
        "id": "industry",
        "kicker": "01",
        "title": "申万一级行业",
        "subtitle": "类别：行业（中文名称）",
        "date_range_label": "2011-2026年",
        "csv_path": DATA_DIR / "industry_ic_analyse.csv",
        "placeholder": False,
    },
    "market": {
        "id": "market",
        "kicker": "02",
        "title": "市值分组",
        "subtitle": "类别：分组编号（1~10）",
        "date_range_label": "2011-2026年",
        "csv_path": DATA_DIR / "market_ic_analyse.csv",
        "placeholder": False,
    },
    "chart4": {
        "id": "chart4",
        "kicker": "03",
        "title": "每月IR",
        "subtitle": "类别：月度时间",
        "date_range_label": "2011-2026年",
        "csv_path": DATA_DIR / "monthly_ic.csv",
        "placeholder": False,
    },
    "chart3": {
        "id": "chart3",
        "kicker": "04",
        "title": "因子超额衰减",
        "subtitle": "类别：持有天数（1~20）",
        "date_range_label": "2011-2026年",
        "csv_path": DATA_DIR / "half_life_20.csv",
        "placeholder": False,
    },
}


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    return response


def isoformat_for_path(file_path: Path) -> str:
    modified = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
    return modified.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_float(raw: str) -> float:
    text = (raw or "").strip()
    if not text:
        raise ValueError("存在空数值")
    return float(text)


def detect_available_metrics(normalized_header: list[str]) -> list[str]:
    metrics: list[str] = []
    if "IC" in normalized_header:
        metrics.append("IC")
    if "IR" in normalized_header:
        metrics.append("IR")
    if "M_IC" in normalized_header and "IC" not in metrics:
        metrics.append("IC")
    if "M_IR" in normalized_header and "IR" not in metrics:
        metrics.append("IR")
    if not metrics:
        raise ValueError(f"{normalized_header} 中缺少 IC 或 IR 列")
    return metrics


def load_chart_rows(file_path: Path) -> tuple[list[dict[str, float | str]], list[str]]:
    if not file_path.exists():
        raise FileNotFoundError(f"数据文件不存在: {file_path.name}")

    with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if not header:
            return []

        normalized_header = [column.strip().upper() for column in header]
        label_index = 0

        available_metrics = detect_available_metrics(normalized_header)
        metric_indexes: dict[str, int] = {}
        for metric in available_metrics:
            aliases = [metric]
            if metric == "IC":
                aliases.append("M_IC")
            if metric == "IR":
                aliases.append("M_IR")

            metric_indexes[metric] = next(
                normalized_header.index(alias)
                for alias in aliases
                if alias in normalized_header
            )

        rows: list[dict[str, float | str]] = []
        for row in reader:
            if not row or not any(cell.strip() for cell in row):
                continue

            label = row[label_index].strip() if len(row) > label_index else ""
            if not label:
                continue

            record: dict[str, float | str] = {"label": label}
            for metric, metric_index in metric_indexes.items():
                record[metric] = parse_float(row[metric_index] if len(row) > metric_index else "")
            rows.append(record)

    return rows, available_metrics


def build_chart_meta() -> list[dict[str, str]]:
    return [
        {
            "id": chart["id"],
            "kicker": chart["kicker"],
            "title": chart["title"],
            "subtitle": chart["subtitle"],
            "dateRangeLabel": chart["date_range_label"],
        }
        for chart in CHART_REGISTRY.values()
    ]


@app.get("/api/charts")
def get_charts():
    return jsonify(build_chart_meta())


@app.get("/api/charts/<chart_id>/data")
def get_chart_data(chart_id: str):
    chart = CHART_REGISTRY.get(chart_id)
    if chart is None:
        return jsonify({"error": "图表不存在"}), 404

    if chart["placeholder"] or chart["csv_path"] is None:
        return jsonify({"id": chart_id, "rows": [], "updatedAt": None, "availableMetrics": []})

    file_path = Path(chart["csv_path"])
    try:
        rows, available_metrics = load_chart_rows(file_path)
    except (FileNotFoundError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 500

    return jsonify(
        {
            "id": chart_id,
            "rows": rows,
            "updatedAt": isoformat_for_path(file_path),
            "availableMetrics": available_metrics,
        }
    )


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5001"))
    app.run(host=host, port=port, debug=True)
