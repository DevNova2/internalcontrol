import os
from pathlib import Path

TRADE_DATA_ROOT = Path(
    os.environ.get(
        "TRADE_DATA_ROOT",
        "/Volumes/desktop-ldbc05e/test/交易组中间文件存储",
    )
)

# 历史挂载目录保留作迁移参考，不再作为默认实时数据源。
LEGACY_TRADE_DATA_ROOT = Path("/mnt/trade_data")


def monitor_csv_path(product_name: str, trade_date: str) -> Path:
    return TRADE_DATA_ROOT / "data" / product_name / f"{trade_date}-gy.csv"


def turnover_json_path(trade_date: str) -> Path:
    return TRADE_DATA_ROOT / "turnover" / f"{trade_date}.json"


def order_csv_path(product_name: str, trade_date: str) -> Path:
    return TRADE_DATA_ROOT / "order" / product_name / f"{trade_date.replace('-', '')}-order.csv"


def chg_csv_path(product_name: str, trade_date: str) -> Path:
    return TRADE_DATA_ROOT / "data" / product_name / "chg" / f"{trade_date}.csv"


def asset_setting_csv_path(product_name: str, last_trade_date: str | None) -> Path | None:
    if not last_trade_date:
        return None
    return TRADE_DATA_ROOT / "asset_setting" / product_name / f"{last_trade_date}.csv"


def realtime_snapshot_dir(product_name: str, trade_date: str) -> Path:
    return TRADE_DATA_ROOT / "data" / product_name / trade_date
