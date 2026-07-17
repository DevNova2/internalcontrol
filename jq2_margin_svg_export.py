import argparse
import datetime
import json
import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from trade_data_paths import LEGACY_TRADE_DATA_ROOT, monitor_csv_path, turnover_json_path


def ensure_browser_path_from_local_venv():
    if os.environ.get("BROWSER_PATH"):
        return
    local_chrome = Path(
        "/home/roger/sdq/.venv/lib/python3.12/site-packages/choreographer/cli/browser_exe/chrome-linux64/chrome"
    )
    if local_chrome.exists():
        os.environ["BROWSER_PATH"] = str(local_chrome)


def write_svg_with_chrome_bootstrap(fig: go.Figure, output_path: Path):
    try:
        fig.write_image(str(output_path), format="svg")
        return
    except RuntimeError as e:
        msg = str(e)
        if "Kaleido requires Google Chrome" not in msg:
            raise

    # 仅在缺少 Chrome 时尝试自动下载一次，然后重试导出。
    try:
        import kaleido

        chrome_path = kaleido.get_chrome_sync()
        print(f"检测到缺少 Chrome，已自动安装到: {chrome_path}")
    except Exception as install_err:
        raise RuntimeError(
            "导出 SVG 失败：缺少 Chrome，且自动安装失败。\n"
            "可手工执行: plotly_get_chrome\n"
            f"自动安装错误: {install_err}"
        ) from install_err

    fig.write_image(str(output_path), format="svg")


def load_trade_data(trade_file: str):
    try:
        with open(trade_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("sell", {}), data.get("buy", {})
    except Exception:
        return {}, {}


def load_realtime_df(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path, index_col=0)
    df.index = [i[:-3] for i in df.index]
    df.fillna(0, inplace=True)
    return df


def create_individual_figure(df: pd.DataFrame, buy: dict, sell: dict, selected_stocks: list[str], title: str):
    fig = go.Figure()

    for stk in buy.get(title, []):
        code = stk[2:] + "." + stk[:2]
        if code in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[code], mode="lines", name=code, line=dict(color="#C36532")))

    for stk in sell.get(title, []):
        code = stk[2:] + "." + stk[:2]
        if code in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[code], mode="lines", name=code, line=dict(color="#0070C0")))

    for stk in selected_stocks:
        if stk in df.columns:
            line_color = "#C36532" if df[stk].iloc[-1] > df[stk].iloc[0] else "#0070C0"
            fig.add_trace(go.Scatter(x=df.index, y=df[stk], mode="lines", name=stk, line=dict(color=line_color)))

    fig.update_yaxes(title_text="Individual Stock Value")
    fig.update_xaxes(tickangle=90)
    fig.update_layout(height=600, width=1200, title_text="换仓数据", showlegend=False)
    return fig


def create_total_figure(df: pd.DataFrame):
    total = df.sum(axis=1)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=total,
            mode="lines",
            name="total",
            line=dict(color="#0070C0"),
            fill="tonexty",
            fillcolor="rgba(109,152,190,0.5)",
        )
    )

    if len(df.index) > 0 and df.index[-1] >= "09:40":
        total_after_931 = total[df.index >= "09:31"]
        if len(total_after_931) > 0:
            max_total = total_after_931.max()
            min_total = total_after_931.min()
            delta = max_total - min_total
            fig.update_yaxes(title_text="Total Value", range=[min_total - delta, max_total + delta])
        else:
            fig.update_yaxes(title_text="Total Value")
    else:
        fig.update_yaxes(title_text="Total Value")

    fig.update_xaxes(tickangle=90)
    fig.update_layout(height=600, width=1200, title_text="总市值", showlegend=True)
    return fig


def create_median_deviation_figure(df: pd.DataFrame, excluded_stocks: list[str]):
    def _hex_to_rgb(hex_color: str):
        c = hex_color.lstrip("#")
        return tuple(int(c[i : i + 2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(rgb: tuple[int, int, int]):
        return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"

    def _interpolate_hex(start_hex: str, end_hex: str, t: float):
        t = max(0.0, min(1.0, t))
        s = _hex_to_rgb(start_hex)
        e = _hex_to_rgb(end_hex)
        mixed = tuple(int(round(s[i] + (e[i] - s[i]) * t)) for i in range(3))
        return _rgb_to_hex(mixed)

    work_df = df.drop(columns=excluded_stocks, errors="ignore")
    fig = go.Figure()
    if work_df.empty:
        fig.update_layout(height=1800, width=1200, title_text="中位数偏离")
        return fig

    last_row = work_df.iloc[-1].sort_values()
    median_value = last_row.median()
    if median_value == 0:
        deviation = pd.Series(0.0, index=last_row.index)
    else:
        deviation = last_row / median_value - 1

    pos_max = deviation[deviation >= 0].max() if (deviation >= 0).any() else 0
    neg_min = deviation[deviation < 0].min() if (deviation < 0).any() else 0

    marker_color = []
    for v in deviation.values:
        if v >= 0:
            t = (v / pos_max) if pos_max > 0 else 0
            marker_color.append(_interpolate_hex("#6F8CB7", "#001042", t))
        else:
            t = (abs(v) / abs(neg_min)) if neg_min < 0 else 0
            marker_color.append(_interpolate_hex("#88A4CB", "#0070C0", t))

    fig.add_trace(
        go.Bar(
            y=last_row.index,
            x=deviation.values,
            orientation="h",
            marker_color=marker_color,
            text=[f"{v:.2%}" for v in deviation.values],
            textposition="auto",
        )
    )
    fig.update_xaxes(title_text="Deviation from Median Value", zeroline=True, zerolinecolor="black")
    fig.update_yaxes(title_text="Stock")
    fig.update_layout(height=1800, width=1200, showlegend=False, title_text="中位数偏离")
    return fig


def parse_args():
    today = datetime.date.today().isoformat()
    parser = argparse.ArgumentParser(description="导出换仓数据/总市值/中位数偏离三张图为 SVG")
    parser.add_argument("--product-name", default="进取2-东北-两融")
    parser.add_argument("--today", default=today)
    parser.add_argument("--file-path", default=None, help="realtime csv，默认按 product-name/today 生成")
    parser.add_argument("--trade-file", default=None, help="turnover json，默认 TRADE_DATA_ROOT/turnover/{today}.json")
    parser.add_argument("--title", default="jq2", help="trade json 中 buy/sell 的 key，如 jq2")
    parser.add_argument("--turn-selected", nargs="*", default=[], help="额外包含的股票，如 SH.600000")
    parser.add_argument("--dev-exclude", nargs="*", default=[], help="中位数图排除的股票")
    parser.add_argument("--output-dir", default="./svg_output")
    return parser.parse_args()


def main():
    args = parse_args()
    ensure_browser_path_from_local_venv()

    # 旧路径保留作迁移参考，不再作为默认实时数据源:
    # file_path = args.file_path or f"{LEGACY_TRADE_DATA_ROOT}/position/realtime/{args.product_name}/{args.today}-gy.csv"
    # trade_file = args.trade_file or f"{LEGACY_TRADE_DATA_ROOT}/turnover/{args.today}.json"
    file_path = args.file_path or str(monitor_csv_path(args.product_name, args.today))
    trade_file = args.trade_file or str(turnover_json_path(args.today))

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_realtime_df(file_path)
    sell, buy = load_trade_data(trade_file)

    fig_individual = create_individual_figure(df, buy, sell, args.turn_selected, args.title)
    fig_total = create_total_figure(df)
    fig_median = create_median_deviation_figure(df, args.dev_exclude)

    write_svg_with_chrome_bootstrap(fig_individual, out_dir / "individual.svg")
    write_svg_with_chrome_bootstrap(fig_total, out_dir / "total.svg")
    write_svg_with_chrome_bootstrap(fig_median, out_dir / "median_deviation.svg")

    print(f"已导出: {out_dir / 'individual.svg'}")
    print(f"已导出: {out_dir / 'total.svg'}")
    print(f"已导出: {out_dir / 'median_deviation.svg'}")


if __name__ == "__main__":
    main()
