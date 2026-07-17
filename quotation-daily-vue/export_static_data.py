#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from urllib.parse import quote_plus

import pymongo

import server


def parse_args():
    parser = argparse.ArgumentParser(description="导出 quotation-daily-vue 静态日数据")
    parser.add_argument("--days", type=int, default=10, help="导出最近 N 个交易日，默认 10")
    return parser.parse_args()


def latest_trade_dates(db_stat, days):
    dates = db_stat["quo_chg"].distinct("date")
    dates = sorted(dates, reverse=True)
    return dates[:days]


def export_one_day(trade_date, db_stat, db_wind, db_jq, out_dir):
    bin_docs = list(
        db_stat["quo_bins"].find(
            {"date": trade_date},
            {"_id": 0, "bins": 1, "daily": 1},
            batch_size=1000000,
        ).sort("bins", 1)
    )
    price_docs = list(
        db_wind["w_vol_price"].find(
            {"date": trade_date},
            {"_id": 0, "code": 1, "pct_chg": 1},
            batch_size=1000000,
        )
    )
    info_docs = list(
        db_wind["w_basic_info"].find(
            {"date": trade_date},
            {"_id": 0, "code": 1, "industry_gics": 1, "industry": 1},
            batch_size=1000000,
        )
    )
    valuation_docs = list(
        db_jq["jq_daily_valuation"].find(
            {"date": trade_date},
            {"_id": 0, "code": 1, "market_cap": 1, "circulating_market_cap": 1},
            batch_size=1000000,
        )
    )
    payload = server.build_payload(
        trade_date,
        bin_docs,
        price_docs,
        info_docs,
        valuation_docs,
        generated_at=trade_date,
    )
    output_path = out_dir / f"daily-{trade_date}.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path, payload


def main():
    args = parse_args()
    out_dir = Path(__file__).resolve().parent / "public" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    stat_client = pymongo.MongoClient("mongodb://192.168.1.77:27017/", serverSelectionTimeoutMS=5000)
    wind_client = pymongo.MongoClient(
        f"mongodb://{quote_plus('Tom')}:{quote_plus('tom')}@192.168.1.99:29900/",
        serverSelectionTimeoutMS=5000,
    )

    db_stat = stat_client["statistic"]
    db_wind = wind_client["basic_wind"]
    db_jq = wind_client["basic_jq"]
    trade_dates = latest_trade_dates(db_stat, args.days)

    if not trade_dates:
        raise SystemExit("未找到可导出的交易日")

    for trade_date in trade_dates:
        output_path, payload = export_one_day(trade_date, db_stat, db_wind, db_jq, out_dir)
        non_zero_industries = sum(1 for item in payload["industryGroups"] if item["count"] > 0)
        print(f"{trade_date} -> {output_path.name} | 市值:{len(payload['marketGroups'])} 行业:{non_zero_industries} 分布:{len(payload['distribution'])}")


if __name__ == "__main__":
    main()
