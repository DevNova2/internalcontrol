#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


def normalize_name(value: Any) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\n", "").replace("\r", "").strip()
    return text or "未命名产品"


def build_payload(xlsx_path: Path) -> dict[str, Any]:
    raw = pd.read_excel(xlsx_path, sheet_name=0, header=None)
    if raw.empty or len(raw) < 2:
        raise ValueError("Excel 内容为空，无法生成图表数据")

    header_index = None
    for idx, row in raw.iterrows():
        if pd.isna(row.iloc[0]) and row.iloc[1:].notna().any():
            header_index = idx
            break

    if header_index is None:
        raise ValueError("未找到有效表头行")

    header_row = raw.iloc[header_index].tolist()
    columns = ["date"] + [normalize_name(item) for item in header_row[1:]]
    data_frame = raw.iloc[header_index + 1 :].copy()
    data_frame.columns = columns
    data_frame = data_frame.dropna(how="all")
    data_frame["date"] = pd.to_datetime(data_frame["date"], errors="coerce")
    data_frame = data_frame[data_frame["date"].notna()].copy()
    data_frame["date"] = data_frame["date"].dt.strftime("%Y-%m-%d")

    payload: dict[str, Any] = {
        "dates": data_frame["date"].tolist(),
        "data": {},
    }

    for column in columns[1:]:
        series = pd.to_numeric(data_frame[column], errors="coerce")
        payload["data"][column] = [
            None if pd.isna(value) else round(float(value), 6)
            for value in series
        ]

    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="将浩池 Excel 转换为 Vue 前端使用的静态 JSON"
    )
    parser.add_argument("--xlsx", required=True, help="输入 Excel 路径")
    parser.add_argument("--out", required=True, help="输出 JSON 路径")
    args = parser.parse_args()

    xlsx_path = Path(args.xlsx).expanduser().resolve()
    output_path = Path(args.out).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = build_payload(xlsx_path)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"已生成: {output_path}")
    print(f"日期数: {len(payload['dates'])}")
    print(f"产品数: {len(payload['data'])}")


if __name__ == "__main__":
    main()
