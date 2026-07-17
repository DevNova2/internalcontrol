#!/usr/bin/env python3
import json
import math
import mimetypes
import os
import posixpath
from calendar import monthrange
from collections import defaultdict
from datetime import date
from decimal import Decimal
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"
DATA_DIR = PUBLIC_DIR / "data"
TOM_MONGO_URL = os.environ.get(
    "QUOTATION_TOM_MONGO_URL",
    "mongodb://Tom:tom@192.168.30.195:29900/admin?authSource=admin",
)
HOST = os.environ.get("QUOTATION_HOST", "127.0.0.1")
PORT = int(os.environ.get("QUOTATION_PORT", "5581"))

INDUSTRY_ORDER = [
    "传媒",
    "电力设备",
    "电子",
    "房地产",
    "纺织服饰",
    "非银金融",
    "钢铁",
    "公用事业",
    "国防军工",
    "环保",
    "机械设备",
    "基础化工",
    "计算机",
    "家用电器",
    "建筑材料",
    "建筑装饰",
    "交通运输",
    "煤炭",
    "美容护理",
    "农林牧渔",
    "汽车",
    "轻工制造",
    "商贸零售",
    "社会服务",
    "石油石化",
    "食品饮料",
    "通信",
    "医药生物",
    "银行",
    "有色金属",
    "综合",
]

RANGE_PRESETS = {
    "oneMonth": lambda end_date: shift_months(end_date, -1),
    "threeMonth": lambda end_date: shift_months(end_date, -3),
    "halfYear": lambda end_date: shift_months(end_date, -6),
    "thisYear": lambda end_date: date(end_date.year, 1, 1),
}

RANGE_PRESET_LABELS = {
    "oneMonth": "近1月",
    "threeMonth": "近3月",
    "halfYear": "近半年",
    "thisYear": "今年",
}


def json_default(value):
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "item"):
        return value.item()
    return str(value)


def format_percent(value):
    return f"{value:.2%}"


def to_float(value, fallback=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def normalize_range_pct_chg(value):
    pct_chg = to_float(value)
    return pct_chg / 100.0 if abs(pct_chg) > 1 else pct_chg


def normalize_requested_date(requested_date):
    return date.today().isoformat() if requested_date == "latest" else requested_date


def parse_iso_date(value, label):
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label}格式错误，应为 YYYY-MM-DD") from exc


def shift_months(base_date, months):
    month_index = base_date.month - 1 + months
    target_year = base_date.year + month_index // 12
    target_month = month_index % 12 + 1
    target_day = min(base_date.day, monthrange(target_year, target_month)[1])
    return date(target_year, target_month, target_day)


def resolve_trade_date_from_tom(base_client, requested_date):
    requested_upper = normalize_requested_date(requested_date)
    base_wind = base_client["basic_wind"]
    base_jq = base_client["basic_jq"]
    economic = base_client["economic"]

    date_upper = requested_upper
    if "trade_dates" in economic.list_collection_names():
        trade_doc = economic["trade_dates"].find_one(
            {"trade_date": {"$lte": requested_upper}},
            {"_id": 0, "trade_date": 1},
            sort=[("trade_date", -1)],
        )
        if trade_doc and trade_doc.get("trade_date"):
            date_upper = trade_doc["trade_date"]

    price_dates = set(
        trade_date
        for trade_date in base_wind["w_vol_price"].distinct("date", {"date": {"$lte": date_upper}})
        if trade_date
    )
    info_dates = set(
        trade_date
        for trade_date in base_wind["w_basic_info"].distinct("date", {"date": {"$lte": date_upper}})
        if trade_date
    )
    valuation_dates = set(
        trade_date
        for trade_date in base_jq["jq_daily_valuation"].distinct("date", {"date": {"$lte": date_upper}})
        if trade_date
    )

    common_dates = sorted(price_dates & info_dates & valuation_dates)
    if not common_dates:
        raise LookupError(f"{requested_upper} 之前未找到三张业务表共同可用的交易日")
    return common_dates[-1]


def resolve_price_trade_date_on_or_before(base_client, requested_date):
    requested_upper = normalize_requested_date(requested_date)
    base_wind = base_client["basic_wind"]
    price_doc = base_wind["w_vol_price"].find_one(
        {"date": {"$lte": requested_upper}},
        {"_id": 0, "date": 1},
        sort=[("date", -1)],
    )
    if not price_doc or not price_doc.get("date"):
        raise LookupError(f"{requested_upper} 之前未找到 w_vol_price 交易日")
    return price_doc["date"]


def resolve_price_trade_dates_in_range(base_client, requested_start, requested_end):
    base_wind = base_client["basic_wind"]
    trade_dates = sorted(
        trade_date
        for trade_date in base_wind["w_vol_price"].distinct(
            "date",
            {"date": {"$gte": requested_start, "$lte": requested_end}},
        )
        if trade_date
    )
    if not trade_dates:
        raise LookupError(f"{requested_start} 至 {requested_end} 未找到 w_vol_price 交易日")
    return trade_dates


def resolve_snapshot_date(collection, requested_upper, table_name):
    snapshot_doc = collection.find_one(
        {"date": {"$lte": requested_upper}},
        {"_id": 0, "date": 1},
        sort=[("date", -1)],
    )
    if not snapshot_doc or not snapshot_doc.get("date"):
        raise LookupError(f"{requested_upper} 之前未找到 {table_name} 数据")
    return snapshot_doc["date"]


def group_sort_key(item):
    group = str(item["group"])
    try:
        return int(group)
    except ValueError:
        return group


def color_for_change(value):
    if value > 0:
        return "red"
    if value < 0:
        return "green"
    return "#7b8798"


def local_payload_candidates():
    return sorted(DATA_DIR.glob("daily-*.json"))


def resolve_local_payload_path(requested_date):
    files = local_payload_candidates()
    if not files:
        return None

    dated_files = sorted(
        (file_path.stem.removeprefix("daily-"), file_path)
        for file_path in files
    )
    if requested_date == "latest":
        return dated_files[-1][1]

    eligible = [file_path for trade_date, file_path in dated_files if trade_date <= requested_date]
    return eligible[-1] if eligible else None


def load_local_payload(requested_date):
    payload_path = resolve_local_payload_path(requested_date)
    if payload_path is None:
        return None
    return json.loads(payload_path.read_text(encoding="utf-8"))


def parse_industry_levels(info_doc):
    raw_value = str(info_doc.get("industry_gics") or info_doc.get("industry") or "").strip()
    return [part.strip() for part in raw_value.split("--") if part.strip()]


def map_industry_name(info_doc):
    level1, level2, level3, level4 = (parse_industry_levels(info_doc) + ["", "", "", ""])[:4]

    if level3 == "综合类Ⅲ":
        return "综合"
    if level2 == "银行" or level3 == "商业银行":
        return "银行"
    if level2 in {"多元金融", "保险Ⅱ"} or level3 in {"资本市场", "多元金融服务", "保险Ⅲ"}:
        return "非银金融"
    if level2 == "媒体Ⅱ" or level3 == "媒体Ⅲ":
        return "传媒"
    if level3 == "航空航天与国防Ⅲ":
        return "国防军工"
    if level2 == "房地产Ⅱ" or level3 == "房地产管理和开发":
        return "房地产"
    if level2 == "公用事业Ⅱ" or level1 == "公用事业":
        return "公用事业"
    if level4 == "环境与设施服务":
        return "环保"
    if level2 == "运输" or level3 in {"交通基础设施", "海运Ⅲ", "航空Ⅲ", "航空货运与物流Ⅲ", "公路与铁路运输"}:
        return "交通运输"
    if level2 == "汽车与汽车零部件" or level3 in {"汽车", "汽车零配件"}:
        return "汽车"
    if level3 in {"软件", "信息技术服务", "互联网软件与服务Ⅲ", "电脑与外围设备"}:
        return "计算机"
    if level3 == "通信设备Ⅲ" or level1 == "电信服务":
        return "通信"
    if level2 in {"技术硬件与设备", "半导体与半导体生产设备"} or level3 in {"电子设备、仪器和元件", "半导体产品与半导体设备"}:
        return "电子"
    if level3 == "电气设备" or level4 in {"电气部件与设备", "重型电气设备"}:
        return "电力设备"
    if level3 == "机械" or level4 in {"工业机械", "建筑机械与重型卡车", "农用农业机械"}:
        return "机械设备"
    if level3 in {"建筑与工程Ⅲ", "建筑产品Ⅲ"}:
        return "建筑装饰"
    if level3 == "建材Ⅲ" or level4 == "建材":
        return "建筑材料"
    if level4 == "钢铁":
        return "钢铁"
    if level4 in {"铝", "铜", "黄金", "贵金属与矿石", "金属非金属"}:
        return "有色金属"
    if level3 == "化工" or level4 in {"基础化工", "特种化工", "化肥与农用化工", "化纤", "多元化工", "工业气体"}:
        return "基础化工"
    if level1 == "能源" or level2 == "能源Ⅱ":
        return "煤炭" if level4 == "煤炭与消费用燃料" else "石油石化"
    if level2 in {"食品、饮料与烟草", "食品与主要用品零售Ⅱ"} or level3 in {"食品", "饮料"}:
        return "食品饮料"
    if level4 == "农产品":
        return "农林牧渔"
    if level3 == "个人用品Ⅲ" or level4 == "个人用品":
        return "美容护理"
    if level2 == "医疗保健设备与服务" or level2 == "制药、生物科技与生命科学" or level1 == "医疗保健":
        return "医药生物"
    if level3 == "纺织品、服装与奢侈品":
        return "纺织服饰"
    if level4 in {"家用电器", "家用器具与特殊消费品"}:
        return "家用电器"
    if level2 == "零售业":
        return "商贸零售"
    if level3 in {"消费品经销商Ⅲ", "专营零售", "互联网与售货目录零售", "多元化零售"}:
        return "商贸零售"
    if level2 == "商业和专业服务":
        return "环保" if level4 == "环境与设施服务" else "社会服务"
    if level2 == "消费者服务Ⅱ" or level3 in {"酒店、餐馆与休闲Ⅲ", "综合消费者服务Ⅲ"}:
        return "社会服务"
    if level3 in {"纸与林木产品", "容器与包装", "家庭用品Ⅲ", "休闲设备与用品"}:
        return "轻工制造"
    if level3 == "家庭耐用消费品" or level4 in {"家庭装饰品", "消费电子产品"}:
        return "家用电器"

    return None


def build_market_groups(price_docs, valuation_docs, group_count=30):
    chg_by_code = {str(doc.get("code")): to_float(doc.get("pct_chg")) for doc in price_docs}
    stocks = []
    for doc in valuation_docs:
        code = str(doc.get("code") or "")
        if not code or code not in chg_by_code:
            continue
        market_cap = to_float(doc.get("market_cap"))
        if market_cap <= 0:
            market_cap = to_float(doc.get("circulating_market_cap"))
        if market_cap <= 0:
            continue
        stocks.append(
            {
                "code": code,
                "marketCap": market_cap,
                "chg": chg_by_code[code],
            }
        )

    if not stocks:
        return []

    stocks.sort(key=lambda item: item["marketCap"], reverse=True)
    total = len(stocks)
    market_groups = []
    for index in range(group_count):
        start = index * total // group_count
        end = (index + 1) * total // group_count
        bucket = stocks[start:end]
        if not bucket:
            continue
        mean_value = sum(item["chg"] for item in bucket) / len(bucket)
        market_groups.append(
            {
                "group": str(index + 1),
                "chgMean": mean_value,
                "color": color_for_change(mean_value),
                "count": len(bucket),
            }
        )
    market_groups.sort(key=group_sort_key)
    return market_groups


def build_distribution_from_price_docs(price_docs):
    bucket_counts = {bin_value: 0 for bin_value in range(-21, 22)}
    for doc in price_docs:
        pct_change = to_float(doc.get("pct_chg")) * 100
        bin_value = math.ceil(pct_change - 0.5)
        if -21 <= bin_value <= 21:
            bucket_counts[bin_value] += 1

    return [
        {
            "bin": bin_value,
            "value": bucket_counts[bin_value],
            "color": "black" if bin_value == 0 else color_for_change(bin_value),
        }
        for bin_value in sorted(bucket_counts)
    ]


def compound_range_price_docs(price_docs):
    compounded = {}
    for doc in price_docs:
        code = str(doc.get("code") or "")
        if not code:
            continue
        pct_change = normalize_range_pct_chg(doc.get("pct_chg"))
        compounded[code] = compounded.get(code, 1.0) * (1.0 + pct_change)

    return [
        {
            "code": code,
            "pct_chg": compounded_value - 1.0,
        }
        for code, compounded_value in compounded.items()
    ]


def build_range_distribution_from_price_docs(price_docs):
    bucket_counts = {bin_value: 0 for bin_value in range(-100, 101)}
    for doc in price_docs:
        pct_change = to_float(doc.get("pct_chg")) * 100
        bin_value = int(round(pct_change))
        bin_value = max(-100, min(100, bin_value))
        bucket_counts[bin_value] += 1

    return [
        {
            "bin": bin_value,
            "value": bucket_counts[bin_value],
            "color": "black" if bin_value == 0 else color_for_change(bin_value),
        }
        for bin_value in range(-100, 101)
    ]


def build_summary(distribution):
    total_count = sum(item["value"] for item in distribution)
    positive_count = sum(item["value"] for item in distribution if item["bin"] > 0)
    negative_count = sum(item["value"] for item in distribution if item["bin"] < 0)
    zero_count = sum(item["value"] for item in distribution if item["bin"] == 0)
    return {
        "positive": format_percent(positive_count / total_count) if total_count else "0.00%",
        "negative": format_percent(negative_count / total_count) if total_count else "0.00%",
        "zero": format_percent(zero_count / total_count) if total_count else "0.00%",
        "total": int(total_count),
    }


def build_industry_groups(price_docs, info_docs):
    chg_by_code = {str(doc.get("code")): to_float(doc.get("pct_chg")) for doc in price_docs}
    grouped = defaultdict(lambda: {"sum": 0.0, "count": 0})
    for info_doc in info_docs:
        code = str(info_doc.get("code") or "")
        industry_name = map_industry_name(info_doc)
        if not code or not industry_name or code not in chg_by_code:
            continue
        grouped[industry_name]["sum"] += chg_by_code[code]
        grouped[industry_name]["count"] += 1

    industry_groups = []
    for industry_name in INDUSTRY_ORDER:
        stats = grouped[industry_name]
        mean_value = stats["sum"] / stats["count"] if stats["count"] else 0.0
        industry_groups.append(
            {
                "group": industry_name,
                "chgMean": mean_value,
                "color": color_for_change(mean_value),
                "count": stats["count"],
            }
        )
    return industry_groups


def build_payload(
    trade_date,
    price_docs,
    info_docs,
    valuation_docs,
    generated_at=None,
    period=None,
    distribution_builder=build_distribution_from_price_docs,
):
    distribution = distribution_builder(price_docs)
    payload = {
        "tradeDate": trade_date,
        "generatedAt": generated_at or date.today().isoformat(),
        "marketGroups": build_market_groups(price_docs, valuation_docs),
        "industryGroups": build_industry_groups(price_docs, info_docs),
        "distribution": distribution,
        "summary": build_summary(distribution),
    }
    if period is not None:
        payload["period"] = period
    return payload


def load_daily_payload_from_tom(requested_date):
    from pymongo import MongoClient

    client = MongoClient(TOM_MONGO_URL, serverSelectionTimeoutMS=4000)
    try:
        client.admin.command("ping")
        trade_date = resolve_trade_date_from_tom(client, requested_date)
        base_wind = client["basic_wind"]
        base_jq = client["basic_jq"]

        price_docs = list(
            base_wind["w_vol_price"].find(
                {"date": trade_date},
                {"_id": 0, "code": 1, "pct_chg": 1},
                batch_size=1000000,
            )
        )
        info_docs = list(
            base_wind["w_basic_info"].find(
                {"date": trade_date},
                {"_id": 0, "code": 1, "industry_gics": 1, "industry": 1},
                batch_size=1000000,
            )
        )
        valuation_docs = list(
            base_jq["jq_daily_valuation"].find(
                {"date": trade_date},
                {"_id": 0, "code": 1, "market_cap": 1, "circulating_market_cap": 1},
                batch_size=1000000,
            )
        )

        if not price_docs:
            raise LookupError(f"{trade_date} 未找到 w_vol_price 数据")
        if not info_docs:
            raise LookupError(f"{trade_date} 未找到 w_basic_info 数据")
        if not valuation_docs:
            raise LookupError(f"{trade_date} 未找到 jq_daily_valuation 数据")

        return build_payload(trade_date, price_docs, info_docs, valuation_docs)
    finally:
        client.close()


def load_daily_payload(requested_date):
    try:
        return load_daily_payload_from_tom(requested_date)
    except Exception as exc:
        local_payload = load_local_payload(requested_date)
        if local_payload is not None:
            print(f"Tom Mongo 读取失败，回退本地 JSON: {exc}")
            return local_payload
        raise


def resolve_range_bounds(base_client, requested_start=None, requested_end=None, preset=None):
    latest_trade_date = resolve_price_trade_date_on_or_before(base_client, "latest")
    latest_trade_day = date.fromisoformat(latest_trade_date)
    mode_label = "自定义区间"

    if preset:
        if preset not in RANGE_PRESETS:
            raise ValueError(f"不支持的 preset: {preset}")
        requested_end = latest_trade_date
        requested_start = RANGE_PRESETS[preset](latest_trade_day).isoformat()
        mode_label = RANGE_PRESET_LABELS[preset]

    if not requested_start or not requested_end:
        raise ValueError("start 和 end 必须同时提供")

    start_day = parse_iso_date(requested_start, "start")
    end_day = parse_iso_date(requested_end, "end")
    if start_day > end_day:
        raise ValueError("start 不能晚于 end")

    trade_dates = resolve_price_trade_dates_in_range(base_client, start_day.isoformat(), end_day.isoformat())
    return trade_dates[0], trade_dates[-1], trade_dates, mode_label


def load_range_payload_from_tom(requested_start=None, requested_end=None, preset=None):
    from pymongo import MongoClient

    client = MongoClient(TOM_MONGO_URL, serverSelectionTimeoutMS=4000)
    try:
        client.admin.command("ping")
        start_trade_date, end_trade_date, trade_dates, mode_label = resolve_range_bounds(
            client,
            requested_start=requested_start,
            requested_end=requested_end,
            preset=preset,
        )
        base_wind = client["basic_wind"]
        base_jq = client["basic_jq"]

        price_docs = list(
            base_wind["w_vol_price"].find(
                {"date": {"$gte": start_trade_date, "$lte": end_trade_date}},
                {"_id": 0, "date": 1, "code": 1, "pct_chg": 1},
                batch_size=1000000,
            )
        )
        compounded_price_docs = compound_range_price_docs(price_docs)
        if not compounded_price_docs:
            raise LookupError(f"{start_trade_date} 至 {end_trade_date} 未找到有效区间行情数据")

        info_date = resolve_snapshot_date(base_wind["w_basic_info"], end_trade_date, "w_basic_info")
        valuation_date = resolve_snapshot_date(base_jq["jq_daily_valuation"], end_trade_date, "jq_daily_valuation")

        info_docs = list(
            base_wind["w_basic_info"].find(
                {"date": info_date},
                {"_id": 0, "code": 1, "industry_gics": 1, "industry": 1},
                batch_size=1000000,
            )
        )
        valuation_docs = list(
            base_jq["jq_daily_valuation"].find(
                {"date": valuation_date},
                {"_id": 0, "code": 1, "market_cap": 1, "circulating_market_cap": 1},
                batch_size=1000000,
            )
        )

        if not info_docs:
            raise LookupError(f"{info_date} 未找到 w_basic_info 数据")
        if not valuation_docs:
            raise LookupError(f"{valuation_date} 未找到 jq_daily_valuation 数据")

        return build_payload(
            end_trade_date,
            compounded_price_docs,
            info_docs,
            valuation_docs,
            distribution_builder=build_range_distribution_from_price_docs,
            period={
                "startDate": start_trade_date,
                "endDate": end_trade_date,
                "tradeDays": len(trade_dates),
                "modeLabel": mode_label,
            },
        )
    finally:
        client.close()


class QuotationHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parsed = urlparse(path)
        if parsed.path == "/":
            return str(PUBLIC_DIR / "index.html")
        clean_path = posixpath.normpath(unquote(parsed.path))
        parts = [part for part in clean_path.split("/") if part and part not in (os.curdir, os.pardir)]
        return str(PUBLIC_DIR.joinpath(*parts))

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/daily":
            self.handle_daily_api(parsed)
            return
        if parsed.path == "/api/range":
            self.handle_range_api(parsed)
            return
        if parsed.path == "/health":
            self.send_json({"ok": True})
            return
        super().do_GET()

    def handle_daily_api(self, parsed):
        params = parse_qs(parsed.query)
        requested_date = params.get("date", ["latest"])[0] or "latest"
        try:
            payload = load_daily_payload(requested_date)
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=502)
            return
        self.send_json(payload)

    def handle_range_api(self, parsed):
        params = parse_qs(parsed.query)
        requested_start = params.get("start", [""])[0]
        requested_end = params.get("end", [""])[0]
        preset = params.get("preset", [""])[0]
        try:
            payload = load_range_payload_from_tom(
                requested_start=requested_start or None,
                requested_end=requested_end or None,
                preset=preset or None,
            )
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=502)
            return
        self.send_json(payload)

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False, default=json_default).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        if self.path.endswith(".js"):
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
        elif self.path.endswith(".css"):
            self.send_header("Content-Type", "text/css; charset=utf-8")
        elif self.path.endswith(".svg"):
            self.send_header("Content-Type", "image/svg+xml")
        else:
            mime, _ = mimetypes.guess_type(self.path)
            if mime:
                self.send_header("Content-Type", mime)
        super().end_headers()


def main():
    os.chdir(PUBLIC_DIR)
    server = ThreadingHTTPServer((HOST, PORT), QuotationHandler)
    print(f"当日盘面涨跌分布 Vue 展示页已启动: http://127.0.0.1:{PORT}")
    print(f"Tom Mongo: {TOM_MONGO_URL}")
    server.serve_forever()


if __name__ == "__main__":
    main()
