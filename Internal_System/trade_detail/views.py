#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/10 17:16
# @Author  : Neo
# @File    : views.py
# @Software: PyCharm
# 说明:
#%%
import json
import sys
from io import StringIO
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
sys.path.append("D:\company_project\ShuiDQReport")

from django.http import JsonResponse
from django.shortcuts import render
import pandas as pd
from Datas.db_client import get_client
from plotly import graph_objs as go
from trade_data_paths import (
    LEGACY_TRADE_DATA_ROOT,
    TRADE_DATA_ROOT,
    monitor_csv_path,
    order_csv_path,
    realtime_snapshot_dir,
    turnover_json_path,
)

pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('expand_frame_repr', False)
pd.set_option('display.max_columns', None)
pd.set_option('display.precision', 14)

SAMPLE_DATA_ROOT = PROJECT_ROOT / 'vue-internal-control' / 'public' / 'data'
INTERNAL_CONTROL_PRODUCTS = {
    'gy': {
        'id': 'gy',
        'label': '进取1-中信-股衍',
        'product_name': '进取1-中信-股衍',
    },
    'jq2': {
        'id': 'jq2',
        'label': '进取2-东北-两融',
        'product_name': '进取2-东北-两融',
    },
    'jq3': {
        'id': 'jq3',
        'label': '进取3-粤开-两融',
        'product_name': '进取3-粤开-两融',
    },
    'yk': {
        'id': 'yk',
        'label': '屿阔-中金-两融',
        'product_name': '屿阔-中金-两融',
    },
}
INTERNAL_CONTROL_CONFIG = {
    'default_product': 'gy',
    'default_monitor_date': '2026-04-20',
    'settlement_sample_date': '2024-09-25',
    'model_sample_date': '2024-11-15',
}


def _fig_to_html(fig, include_plotlyjs=False):
    return fig.to_html(
        full_html=False,
        include_plotlyjs='cdn' if include_plotlyjs else False,
        config={'displayModeBar': False, 'responsive': True},
    )


def _style_figure(fig, title, height):
    fig.update_layout(
        autosize=True,
        height=height,
        title=title,
        font={'size': 16},
        paper_bgcolor='white',
        plot_bgcolor='#edf2f7',
        margin={'l': 56, 'r': 32, 't': 64, 'b': 56},
        legend={
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'right',
            'x': 1,
        },
    )
    fig.update_xaxes(showgrid=True, gridcolor='#dbe3ef', tickangle=90)
    fig.update_yaxes(showgrid=True, gridcolor='#dbe3ef')
    return fig


def _get_internal_control_product(product_id):
    product = INTERNAL_CONTROL_PRODUCTS.get(product_id)
    if product:
        return product
    return INTERNAL_CONTROL_PRODUCTS[INTERNAL_CONTROL_CONFIG['default_product']]


def _candidate_encodings():
    return ('utf-8', 'utf-8-sig', 'gb18030', 'gbk')


def _read_text_file(file_path):
    last_error = None
    for encoding in _candidate_encodings():
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def _read_csv_file(file_path):
    last_error = None
    for encoding in _candidate_encodings():
        try:
            return pd.read_csv(file_path, encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    return pd.read_csv(file_path)


def _load_turnover_payload(trade_date):
    return json.loads(_read_text_file(turnover_json_path(trade_date)))


def _sample_monitor_csv_path(product_name):
    return SAMPLE_DATA_ROOT / product_name / f"{INTERNAL_CONTROL_CONFIG['default_monitor_date']}-gy.csv"


def _sample_turnover_json_path():
    return SAMPLE_DATA_ROOT / 'common' / f"{INTERNAL_CONTROL_CONFIG['default_monitor_date']}.json"


def _sample_settlement_csv_path():
    return SAMPLE_DATA_ROOT / '阿尔法1号-交易细节' / INTERNAL_CONTROL_CONFIG['settlement_sample_date'] / 'dma_zx.csv'


def _sample_model_csv_path():
    return SAMPLE_DATA_ROOT / '阿尔法1号-长江两融' / INTERNAL_CONTROL_CONFIG['model_sample_date'] / 'minute_cj_first_v2_0.csv'


def _normalize_columns(df):
    df = df.copy()
    df.columns = [str(column).strip().replace('\ufeff', '') for column in df.columns]
    return df


def _parse_time_text(raw_value):
    text = str(raw_value or '').strip()
    if not text:
        return ''
    if ':' in text:
        parts = text.split(':')
        if len(parts) >= 2:
            if len(parts) >= 3:
                return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2].zfill(2)[:2]}"
            return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}"
    digits = ''.join(char for char in text if char.isdigit())
    if len(digits) >= 6:
        return f'{digits[0:2]}:{digits[2:4]}:{digits[4:6]}'
    if len(digits) == 4:
        return f'{digits[0:2]}:{digits[2:4]}'
    return text[:8]


def _snapshot_time_from_name(file_name):
    digits = ''.join(char for char in Path(file_name).stem if char.isdigit())
    if len(digits) < 6:
        return ''
    return f'{digits[0:2]}:{digits[2:4]}:{digits[4:6]}'


def _normalize_order_side(raw_value):
    text = str(raw_value or '').strip().lower()
    if not text:
        return ''
    if 'sell' in text or '卖' in text:
        return 'sell'
    if 'buy' in text or '买' in text:
        return 'buy'
    return ''


def _list_turnover_dates():
    turnover_dir = TRADE_DATA_ROOT / 'turnover'
    if not turnover_dir.exists():
        return []
    dates = []
    for json_path in turnover_dir.glob('*.json'):
        date_text = json_path.stem
        if len(date_text) == 10:
            dates.append(date_text)
    return sorted(set(dates))


def _minute_snapshot_files(product_name, trade_date):
    minute_dir = realtime_snapshot_dir(product_name, trade_date)
    if not minute_dir.exists():
        return minute_dir, []
    return minute_dir, sorted(minute_dir.glob('*-gy-data.csv'))


def _is_trade_date_ready(product_name, trade_date):
    minute_dir, minute_files = _minute_snapshot_files(product_name, trade_date)
    return (
        monitor_csv_path(product_name, trade_date).exists()
        and turnover_json_path(trade_date).exists()
        and order_csv_path(product_name, trade_date).exists()
        and minute_dir.exists()
        and bool(minute_files)
    )


def _list_monitor_dates(product_name):
    available_dates = []
    for trade_date in _list_turnover_dates():
        if _is_trade_date_ready(product_name, trade_date):
            available_dates.append(trade_date)
    return available_dates


def _resolve_monitor_date(product_name, requested_date=None):
    if requested_date:
        return requested_date

    available_dates = _list_monitor_dates(product_name)
    if available_dates:
        return available_dates[-1]
    return INTERNAL_CONTROL_CONFIG['default_monitor_date']


def _load_monitor_df(product_name, trade_date):
    csv_path = monitor_csv_path(product_name, trade_date)
    raw_df = _read_csv_file(csv_path)
    df = raw_df.set_index(raw_df.columns[0])
    df.index = [str(idx)[:5] for idx in df.index]
    df = df.apply(pd.to_numeric, errors='coerce')
    return df.dropna(axis=1, how='all').fillna(method='ffill').fillna(method='bfill')


def _load_turnover_codes(payload, monitor_key):
    buy_codes = payload.get('buy', {}).get(monitor_key, [])
    sell_codes = payload.get('sell', {}).get(monitor_key, [])
    return buy_codes, sell_codes


def _to_monitor_code(raw_code):
    if not raw_code:
        return raw_code
    if '.' in raw_code:
        return raw_code
    if len(raw_code) < 4:
        return raw_code
    prefix = raw_code[:2].upper()
    if prefix in {'SZ', 'SH'}:
        return f'{raw_code[2:]}.{prefix}'
    return raw_code


def _build_realtime_settlement_dataframe(product_name, trade_date):
    csv_path = order_csv_path(product_name, trade_date)
    if not csv_path.exists():
        raise FileNotFoundError(f'未找到交割单文件: {csv_path}')

    raw_df = _normalize_columns(_read_csv_file(csv_path))
    time_column = 'time' if 'time' in raw_df.columns else '更新时间' if '更新时间' in raw_df.columns else None
    side_column = 'order_side' if 'order_side' in raw_df.columns else '交易' if '交易' in raw_df.columns else None
    price_column = 'order_price' if 'order_price' in raw_df.columns else '成交均价' if '成交均价' in raw_df.columns else None
    volume_column = 'order_volume' if 'order_volume' in raw_df.columns else '成交量' if '成交量' in raw_df.columns else None
    if not all([time_column, side_column, price_column, volume_column]):
        raise FileNotFoundError(f'交割单字段不完整: {csv_path}')

    df = pd.DataFrame({
        'time': raw_df[time_column].map(_parse_time_text),
        'order_side': raw_df[side_column].map(_normalize_order_side),
        'order_price': pd.to_numeric(raw_df[price_column], errors='coerce'),
        'order_volume': pd.to_numeric(raw_df[volume_column], errors='coerce'),
    })
    df = df[(df['time'] != '') & (df['order_side'] != '')].dropna(subset=['order_price', 'order_volume'])
    if df.empty:
        raise FileNotFoundError(f'交割单无可用记录: {csv_path}')

    df = df.sort_values('time').reset_index(drop=True)
    df['order_value'] = df['order_price'] * df['order_volume']
    df['order_value'] = df.apply(
        lambda row: row['order_value'] if row['order_side'] == 'sell' else -row['order_value'],
        axis=1,
    )
    df['net_sum'] = (-df['order_value']).cumsum()
    return df[['time', 'order_value', 'net_sum']]


def _build_realtime_model_dataframe(product, trade_date, turnover_payload):
    minute_dir, minute_files = _minute_snapshot_files(product['product_name'], trade_date)
    if not minute_files:
        raise FileNotFoundError(f'未找到分钟行情目录: {minute_dir}')

    buy_codes, sell_codes = _load_turnover_codes(turnover_payload, product['id'])
    order_type_by_code = {}
    for raw_code in buy_codes:
        order_type_by_code[_to_monitor_code(raw_code)] = 'buy'
    for raw_code in sell_codes:
        order_type_by_code[_to_monitor_code(raw_code)] = 'sell'
    if not order_type_by_code:
        raise FileNotFoundError(f'换仓文件未找到产品 {product["id"]} 的买卖列表: {turnover_json_path(trade_date)}')

    rows = []
    for minute_path in minute_files:
        time_text = _snapshot_time_from_name(minute_path.name)
        if not time_text:
            continue
        minute_df = _normalize_columns(_read_csv_file(minute_path))
        if not {'code', 'lastPrice', 'lastClose'}.issubset(minute_df.columns):
            continue
        minute_df = minute_df[['code', 'lastPrice', 'lastClose']].copy()
        minute_df['code'] = minute_df['code'].astype(str).str.strip()
        minute_df = minute_df[minute_df['code'].isin(order_type_by_code)]
        if minute_df.empty:
            continue
        minute_df['lastPrice'] = pd.to_numeric(minute_df['lastPrice'], errors='coerce')
        minute_df['lastClose'] = pd.to_numeric(minute_df['lastClose'], errors='coerce')
        minute_df = minute_df[
            minute_df['lastPrice'].notna()
            & minute_df['lastClose'].notna()
            & (minute_df['lastClose'] != 0)
        ]
        if minute_df.empty:
            continue
        minute_df['chg_pre'] = minute_df['lastPrice'] / minute_df['lastClose'] - 1
        for row in minute_df.itertuples(index=False):
            rows.append({
                'date': trade_date,
                'order_type': order_type_by_code.get(row.code, ''),
                'time': time_text,
                'code': row.code,
                'chg_pre': row.chg_pre,
            })

    if not rows:
        raise FileNotFoundError(f'分钟行情未生成有效超额差异数据: {minute_dir}')
    return pd.DataFrame(rows, columns=['date', 'order_type', 'time', 'code', 'chg_pre'])


def _create_turn_figure(df, buy_codes, sell_codes):
    fig = go.Figure()
    for raw_code in buy_codes:
        code = _to_monitor_code(raw_code)
        if code in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[code], mode='lines', name=code,
                line={'color': '#d37440', 'width': 1.4},
            ))

    for raw_code in sell_codes:
        code = _to_monitor_code(raw_code)
        if code in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[code], mode='lines', name=code,
                line={'color': '#0070c0', 'width': 1.4},
            ))

    fig.update_yaxes(title_text='Individual Stock Value')
    return _style_figure(fig, '换仓数据', 430)


def _create_deviation_figure(df, excluded_codes):
    work_df = df.drop(columns=excluded_codes, errors='ignore')
    last_row = work_df.iloc[-1].dropna().sort_values()
    median_value = last_row.median()
    if median_value == 0:
        deviation = pd.Series(0.0, index=last_row.index)
    else:
        deviation = last_row / median_value - 1

    pos_max = deviation[deviation >= 0].max() if (deviation >= 0).any() else 0
    neg_min = deviation[deviation < 0].min() if (deviation < 0).any() else 0
    colors = []
    for value in deviation:
        if value >= 0:
            ratio = value / pos_max if pos_max else 0
            colors.append(f'rgba(7, 32, 97, {0.35 + 0.65 * ratio:.3f})')
        else:
            ratio = abs(value) / abs(neg_min) if neg_min else 0
            colors.append(f'rgba(76, 134, 197, {0.30 + 0.60 * ratio:.3f})')

    fig = go.Figure(go.Bar(
        y=deviation.index,
        x=deviation.values,
        orientation='h',
        marker={'color': colors},
        text=[f'{value:.2%}' for value in deviation.values],
        textposition='auto',
        hovertemplate='%{y}<br>偏离: %{x:.2%}<extra></extra>',
    ))
    fig.update_xaxes(title_text='Deviation', tickformat='.0%', zeroline=True, zerolinecolor='#24324b')
    fig.update_yaxes(title_text='Stock')
    return _style_figure(fig, '中位数偏离', 1180)


def _create_dma_settlement_figure(df, title):
    df = df.sort_values('time').copy()
    point_colors = df['order_value'].apply(lambda value: '#c2552d' if value < 0 else '#547fb9')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['time'],
        y=df['net_sum'],
        name='累计净成交',
        line={'color': '#1f77b4', 'width': 2},
        hovertemplate='时间: %{x}<br>累计净成交: %{y:,.0f}<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=df['time'],
        y=df['order_value'],
        mode='markers',
        name='订单金额',
        yaxis='y2',
        marker={'color': point_colors, 'size': 6, 'opacity': 0.78},
        hovertemplate='时间: %{x}<br>订单金额: %{y:,.0f}<extra></extra>',
    ))

    if '14:30' in df['time'].values:
        fig.add_vline(x='14:30', line_width=2, line_dash='dash', line_color='#b04f2c')

    fig.update_layout(
        yaxis={'title': '累计净成交金额'},
        yaxis2={'title': '订单金额（负买，正卖）', 'side': 'right', 'overlaying': 'y'},
    )
    return _style_figure(fig, title, 330)


def _create_model_figure(df, title):
    df = df.copy()
    df['time'] = df['time'].astype(str).str[:5]
    summary = df.groupby(['time', 'order_type'])['chg_pre'].mean().unstack(fill_value=0) * 100
    summary['differ'] = summary.get('sell', 0) - summary.get('buy', 0)

    fig = go.Figure()
    if 'differ' in summary:
        fig.add_trace(go.Scatter(
            x=summary.index, y=summary['differ'], name='differ',
            line={'color': '#202020', 'width': 2},
        ))
    if 'sell' in summary:
        fig.add_trace(go.Scatter(
            x=summary.index, y=summary['sell'], name='sell',
            line={'color': '#4f9ceb', 'width': 1.8},
        ))
    if 'buy' in summary:
        fig.add_trace(go.Scatter(
            x=summary.index, y=summary['buy'], name='buy',
            line={'color': '#de8a59', 'width': 1.8},
        ))

    fig.add_hline(y=0, line_width=2, line_color='red')
    fig.update_yaxes(title_text='收益偏离', ticksuffix='%')
    return _style_figure(fig, title, 330)


def _build_internal_control_payload(product_id, requested_date=None):
    product = _get_internal_control_product(product_id)
    trade_date = _resolve_monitor_date(product['product_name'], requested_date)
    monitor_path = monitor_csv_path(product['product_name'], trade_date)
    turnover_path = turnover_json_path(trade_date)

    if not monitor_path.exists():
        raise FileNotFoundError(f'未找到监控文件: {monitor_path}')
    if not turnover_path.exists():
        raise FileNotFoundError(f'未找到换仓文件: {turnover_path}')

    turnover_payload = _load_turnover_payload(trade_date)
    settlement_df = _build_realtime_settlement_dataframe(product['product_name'], trade_date)
    model_df = _build_realtime_model_dataframe(product, trade_date, turnover_payload)
    minute_dir, _minute_files = _minute_snapshot_files(product['product_name'], trade_date)

    return {
        'product': product['id'],
        'productLabel': product['label'],
        'date': trade_date,
        'tradeDataRoot': str(TRADE_DATA_ROOT),
        'monitorCsv': _read_text_file(monitor_path),
        'turnover': turnover_payload,
        'settlementCsv': settlement_df.to_csv(index=False),
        'modelCsv': model_df.to_csv(index=False),
        'sourceMode': 'realtime',
        'fallbackReason': '',
        'sources': {
            'monitor': str(monitor_path),
            'turnover': str(turnover_path),
            'order': str(order_csv_path(product['product_name'], trade_date)),
            'minuteDir': str(minute_dir),
            'legacyTradeDataRoot': str(LEGACY_TRADE_DATA_ROOT),
        },
    }


def internal_control_api(request):
    product_id = request.GET.get('product') or INTERNAL_CONTROL_CONFIG['default_product']
    requested_date = request.GET.get('date') or None
    if product_id not in INTERNAL_CONTROL_PRODUCTS:
        return JsonResponse({'error': f'不支持的产品: {product_id}'}, status=400, json_dumps_params={'ensure_ascii': False})

    try:
        payload = _build_internal_control_payload(product_id, requested_date)
    except FileNotFoundError as exc:
        return JsonResponse({'error': str(exc)}, status=404, json_dumps_params={'ensure_ascii': False})

    return JsonResponse(payload, json_dumps_params={'ensure_ascii': False})


def internal_control_page(request):
    product = _get_internal_control_product(INTERNAL_CONTROL_CONFIG['default_product'])
    payload = _build_internal_control_payload(product['id'])
    monitor_date = payload['date']
    monitor_df = _load_monitor_df(product['product_name'], monitor_date)
    buy_codes, sell_codes = _load_turnover_codes(payload['turnover'], product['id'])
    excluded_codes = [_to_monitor_code(code) for code in buy_codes + sell_codes]
    settlement_df = pd.read_csv(StringIO(payload['settlementCsv']))
    model_df = pd.read_csv(StringIO(payload['modelCsv']))

    context = {
        'page_title': '内控系统四图总览',
        'monitor_date': monitor_date,
        'trade_detail_date': monitor_date,
        'model_date': monitor_date,
        'turn_chart': _fig_to_html(_create_turn_figure(monitor_df, buy_codes, sell_codes), include_plotlyjs=True),
        'deviation_chart': _fig_to_html(_create_deviation_figure(monitor_df, excluded_codes)),
        'settlement_chart': _fig_to_html(
            _create_dma_settlement_figure(settlement_df, f'交易细节 ~ {product["label"]} [{monitor_date}]')
        ),
        'model_chart': _fig_to_html(
            _create_model_figure(model_df, f'{monitor_date} ~ {product["label"]} 超额差异')
        ),
    }
    return render(request, 'trade_detail/internal_control.html', context)





def _plot(df_plot, pro=None, order_type=None):
    average_sell_value =  df_plot[df_plot['code'] == 'sell']['chg_pre'].mean()
    average_buy_value =  df_plot[df_plot['code'] == 'buy']['chg_pre'].mean()
#---------------------------------------------------------------------------------------------
    #计算分钟平均超额差=（分钟卖平均涨跌幅-分钟买平均涨跌幅）  之后再取平均值  
    '''
    average_diff=average_sell_value-average_buy_value

    db = get_client(c_from='neo')
    t_dongfang= db.trade_detail.alpha_first_dongfang
    t_margin= db.trade_detail.alpha_first_margin
    the_date = next(t_dongfang.find({}, {'_id': 0, 'date': 1}).sort([('date', -1), ]).limit(1)).get('date')
    t_dongfang = pd.DataFrame(t_dongfang.find({'date': the_date}, {'_id': 0}))
    t_margin = pd.DataFrame(t_margin.find({'date': the_date}, {'_id': 0}))

    t_dongfang= t_dongfang[['date','time','stock_code','order_side','order_price','rebalance_or_turn','order_sum','order_volume']].sort_values('time')

    t_dongfang = t_dongfang[t_dongfang['rebalance_or_turn'] != 0]
    t_dongfang_sum=abs(t_dongfang[t_dongfang['order_side'] == 'buy']['order_sum'].sum())+t_dongfang[t_dongfang['order_side'] == 'sell']['order_sum'].sum()


    
    t_margin=t_margin[['date','time','stock_code','order_side','order_price','rebalance_or_turn','order_sum','order_volume']].sort_values('time')
    t_margin = t_margin[t_margin['rebalance_or_turn'] != 0]
    t_margin_sum=abs(t_margin[t_margin['order_side'] == 'buy']['order_sum'].sum())+t_margin[t_margin['order_side'] == 'sell']['order_sum'].sum()
    '''
    average_diff=average_sell_value-average_buy_value
    db = get_client(c_from='neo')
    t_dongfang= db.trade_detail.alpha_first_dongfang
    t_margin= db.trade_detail.alpha_first_margin
    #the_date='2024-08-05'
    the_date = next(t_dongfang.find({}, {'_id': 0, 'date': 1}).sort([('date', -1), ]).limit(1)).get('date')
    #last_date = next(t_dongfang.find({}, {'_id': 0, 'date': 1}).sort([('date', -1), ]).limit(1)).get('date')
    t_dongfang = pd.DataFrame(t_dongfang.find({'date': the_date}, {'_id': 0}))
    t_margin = pd.DataFrame(t_margin.find({'date': the_date}, {'_id': 0}))
    t_dongfang= t_dongfang[['date','time','stock_code','order_side','order_price','rebalance_or_turn','order_sum','order_volume']].sort_values('time')
    t_dongfang = t_dongfang[t_dongfang['rebalance_or_turn'] != 0]
    t_margin=t_margin[['date','time','stock_code','order_side','order_price','rebalance_or_turn','order_sum','order_volume']].sort_values('time')
    t_margin = t_margin[t_margin['rebalance_or_turn'] != 0]

    # %%

    db = get_client(c_from='db_u')
    t_close=db.basic_jq.jq_daily_price_none
    #这里时间是t-1
    db = get_client(c_from='neo')
    t_alpha = db.bt_paper_trade.minute_alpha_first_v2_0
    last_date = next(t_alpha.find({}, {'_id': 0, 'date': 1}).sort([('date', -1)]).skip(1).limit(1)).get('date')
    t_close = pd.DataFrame(t_close.find({'date': last_date}, {'_id': 0}))
    unique_order_sides1 = t_margin['stock_code'].unique().tolist()
    result1 = {}

    for code in unique_order_sides1:
        # 提取股票代码的前6位
        code_prefix = code[:6]

        # 在数据框中查找匹配的行
        matched_row = t_close [t_close ['code_jq'].str.startswith(code_prefix)]

        if not matched_row.empty:
            # 如果找到匹配的行，获取 close 值
            close_value = matched_row['close'].values[0]
            result1[code] = close_value
        else:
            # 如果没有找到匹配的行，将值设为 None 或其他标识符
            result1[code] = None
    #%%
    # 初始化结果变量
    t_margin_total_sum_buy = 0
    t_margin_total_sum_sell = 0

    # 遍历数据框的每一行
    for index, row in t_margin.iterrows():
        if row['order_side'] == 'buy':
            stock_code = row['stock_code']
            if stock_code in result1:
                matched_price = result1[stock_code]
                order_price = row['order_price']
                order_sum = row['order_sum']
                # 计算单个订单的值
                value = (abs(order_sum))* (order_price - matched_price) / matched_price

                # 累加到总和
                t_margin_total_sum_buy += value
        if row['order_side'] == 'sell':
            stock_code = row['stock_code']
            if stock_code in result1:
                matched_price = result1[stock_code]
                order_price = row['order_price']
                order_sum = row['order_sum']
                # 计算单个订单的值
                value = (order_sum)* (order_price - matched_price) / matched_price

                # 累加到总和
                t_margin_total_sum_sell += value

    #东方data
    unique_order_sides2 = t_dongfang['stock_code'].unique().tolist()
    result2 = {}

    for code in unique_order_sides2:
        # 提取股票代码的前6位
        code_prefix = code[:6]

        # 在数据框中查找匹配的行
        matched_row = t_close [t_close ['code_jq'].str.startswith(code_prefix)]

        if not matched_row.empty:
            # 如果找到匹配的行，获取 close 值
            close_value = matched_row['close'].values[0]
            result2[code] = close_value
        else:
            # 如果没有找到匹配的行，将值设为 None 或其他标识符
            result2[code] = None
    #%%
    # 初始化结果变量
    t_dongfang_total_sum_buy = 0
    t_dongfang_total_sum_sell = 0

    # 遍历数据框的每一行
    for index, row in t_dongfang.iterrows():
        if row['order_side'] == 'buy':
            stock_code = row['stock_code']
            if stock_code in result2:
                matched_price = result2[stock_code]
                order_price = row['order_price']
                order_sum = row['order_sum']
                # 计算单个订单的值
                value = (abs(order_sum))* (order_price - matched_price) / matched_price

                # 累加到总和
                t_dongfang_total_sum_buy += value
        if row['order_side'] == 'sell':
            stock_code = row['stock_code']
            if stock_code in result2:
                matched_price = result2[stock_code]
                order_price = row['order_price']
                order_sum = row['order_sum']
                # 计算单个订单的值
                value = (order_sum)* (order_price - matched_price) / matched_price

                # 累加到总和
                t_dongfang_total_sum_sell += value

    #汇总
    t_total_sum_buy=t_margin_total_sum_buy+ t_dongfang_total_sum_buy
    t_total_sum_sell=t_margin_total_sum_sell+ t_dongfang_total_sum_sell  

    t_margin_sum=abs(t_margin[t_margin['order_side'] == 'buy']['order_sum'].sum())+t_margin[t_margin['order_side'] == 'sell']['order_sum'].sum()

    #%%

    t_dongfang_sum=abs(t_dongfang[t_dongfang['order_side'] == 'buy']['order_sum'].sum())+t_dongfang[t_dongfang['order_side'] == 'sell']['order_sum'].sum()

    t_sum=t_dongfang_sum+t_margin_sum


    t_dongfang = t_dongfang.sort_values('time')
    t_margin = t_margin.sort_values('time')
    t_dongfang['time'] = t_dongfang.time.apply(lambda x: x[:5])
    t_margin ['time'] =t_margin .time.apply(lambda x: x[:5])
    t_dongfang['order_value'] = t_dongfang['order_price'] * t_dongfang['order_volume']
    t_margin['order_value'] = t_margin['order_price'] * t_margin['order_volume']
    # 按分钟和 order_side 分组，计算 order_value 的和
    df_grouped1 = t_dongfang.groupby(['time', 'order_side']).agg({'order_value': 'sum'}).reset_index()
    # 按分钟和 order_side 分组，计算 order_value 的和
    df_grouped2 = t_margin.groupby(['time', 'order_side']).agg({'order_value': 'sum'}).reset_index()
    # 重新排列数据框，将 buy 和 sell 的值分别放入新的列
    df_pivo_t_dongfang = df_grouped1.pivot(index='time',columns='order_side', values='order_value').fillna(0).reset_index()
# 重新排列数据框，将 buy 和 sell 的值分别放入新的列
    df_pivo_t_margin= df_grouped2.pivot(index='time', columns='order_side', values='order_value').fillna(0).reset_index()
    for pivot_df in (df_pivo_t_margin, df_pivo_t_dongfang):
        for side in ['buy', 'sell']:
            if side not in pivot_df.columns:
                pivot_df[side] = 0
    # 按照 time 列合并两个数据框
    df_merged = pd.merge( df_pivo_t_margin,df_pivo_t_dongfang,on='time', how='outer', suffixes=('_df1', '_df2'))
    # 填充NaN为0
    df_merged.fillna(0, inplace=True)
    # 计算 buy_sum 和 sell_sum 列
    df_merged['buy_sum'] = df_merged['buy_df1'] + df_merged['buy_df2']
    df_merged['sell_sum'] = df_merged['sell_df1'] + df_merged['sell_df2']
    df_merged['total_sum']=df_merged['buy_sum']+df_merged['sell_sum']
    df_merged['minute_weight']=df_merged['total_sum']/t_sum
    df_merged['buy_weight']=df_merged['buy_sum']/df_merged['buy_sum'].sum()

    df_merged['sell_weight']=df_merged['sell_sum']/df_merged['sell_sum'].sum()

    df_plot=df_plot[['time','code','chg_pre']].sort_values('time')
    merged_df = pd.merge(df_plot, df_merged, on='time', how='left')
    numeric_cols = ['chg_pre', 'minute_weight', 'buy_weight', 'sell_weight']
    merged_df[numeric_cols] = merged_df[numeric_cols].fillna(0)
    merged_df=merged_df[['time','code','chg_pre','minute_weight','buy_weight','sell_weight']].sort_values('time')
    #成交量加权超额差=（分钟卖平均涨跌幅-分钟买平均涨跌幅）*（每分钟买卖量/总的买卖量）之后求和
    #average_volume_diff= ((merged_df[merged_df['code'] == 'sell']['chg_pre'].reset_index(drop=True) - 
                        #merged_df[merged_df['code'] == 'buy']['chg_pre'].reset_index(drop=True)) * 
                       #merged_df[merged_df['code'] == 'sell']['minute_weight'].reset_index(drop=True)).sum()
    #细分成交量加权超额差 = （每分钟卖量/总卖量）*分钟卖平均涨跌幅-（每分钟买量/总买量）*分钟买平均涨跌幅  之后求和

    average_volume_diff_min =(merged_df[merged_df['code'] == 'sell']['chg_pre'].reset_index(drop=True) *merged_df[merged_df['code'] == 'sell']['sell_weight'].reset_index(drop=True)-
                        merged_df[merged_df['code'] == 'buy']['chg_pre'].reset_index(drop=True) * merged_df[merged_df['code'] == 'buy']['buy_weight'].reset_index(drop=True)).sum()
    
# 新增买卖超额差
    dongfang_detail=-(t_dongfang_total_sum_buy - t_dongfang_total_sum_sell)/t_dongfang_sum*100
    b_margin_detail=-(t_margin_total_sum_buy - t_margin_total_sum_sell)/t_margin_sum*100
    #a = -(t_total_sum_buy - t_total_sum_sell) / df_merged['total_sum'].sum()
    total_detail = -(t_total_sum_buy - t_total_sum_sell) /t_sum*100    


    line_list = []
    for code in df_plot.code.unique().tolist():
        df_ = df_plot.loc[df_plot.code == code]
        gs = go.Scatter(x=df_['time'], y=df_['chg_pre'], name=code)
        if code == 'trade':
            gs.update(line=dict(width=3, color='gray'), )
        elif code == 'buy':
            gs.update(line=dict(width=2, color='red'), )
        elif code == 'sell':
            gs.update(line=dict(width=2, color='blue'), )
        elif code == 'differ':
            gs.update(line=dict(width=2, color='black'), )
        line_list.append(gs)
    div = ''
    if order_type == '指数拟合':
        df_ = df_plot.loc[(df_plot.code == 'sell')]
        if not df_.empty:
        
            _s = df_plot.loc[(df_plot.code == 'sell') & (df_plot.time == '09:40')].chg_pre.squeeze()
            _b = df_plot.loc[(df_plot.code == 'buy') & (df_plot.time == '09:40')].chg_pre.squeeze()
            #div = (' ~ 换出：{:.3f}%，换入：{:.3f}%，超额差：{:.3f}% <br> '
            #'分钟平均超额差：{:.3f}% , 买卖分钟成交量加权平均超额差：{:.3f}%').format(
                #float(_s), float(_b), float(_s - _b), float(average_diff), float(average_volume_diff_min))
            div = (' ~ 换出：{:.3f}%，换入：{:.3f}%，超额差：{:.3f}% <br> '
           '分钟平均超额差：{:.3f}% , 成交量加权平均超额差：{:.3f}%   <br> '
           '东方损失：{:.3f}% , 股衍损失：{:.3f}% ,总交易损失：{:.3f}%').format(
            float(_s), float(_b), float(_s - _b), float(average_diff), float(average_volume_diff_min),
            float(dongfang_detail), float(b_margin_detail), float(total_detail),

            '''
            div = (' ~ 换出：{:.3f}%，换入：{:.3f}%，超额差：{:.3f}% <br> '
           .format(
            float(_s), float(_b), float(_s - _b))
            '''
            ) 
        else:
            div = ' ~ 今日无换仓'
    fig = go.Figure(data=line_list,
                    layout={
                        'height': 888,
                        "title": f"{pro} - {order_type}{div}",
                        "font": {"size": 22, },
                        'legend': {'orientation': "v", 'yanchor': 'auto', 'xanchor': 'center', },
                        "xaxis": {"showgrid": False, },
                        "yaxis": {"ticksuffix": "%", "showgrid": True, "zerolinecolor": "red", "zerolinewidth": 3},
                    })

    return fig.to_html(full_html=False, include_plotlyjs=True)


def _return_df(df: pd.DataFrame, pro=None):
    df = df.sort_values('time')

    df['time'] = df.time.apply(lambda x: x[:5])
    df['chg_pre'] = df.chg_pre * 100
    df_buy = df.loc[df.order_type == 'buy', ['time', 'code', 'chg_pre']]
    df_sell = df.loc[df.order_type == 'sell', ['time', 'code', 'chg_pre']]
    df_index = df.loc[df.code.isin(['buy', 'sell', 'trade','differ']), ['time', 'code', 'chg_pre']]



    fig_buy = go.Figure(data=[]).to_html(full_html=False, include_plotlyjs=True)
    fig_sell = fig_buy
    if not df_buy.empty:
        fig_buy = _plot(df_buy, pro, order_type='换入')
        fig_sell = _plot(df_sell, pro, order_type='换出')
    fig_index = _plot(df_index, pro, order_type='指数拟合')

    return fig_buy, fig_sell, fig_index
    
    
def calculate_difference(group, group_key=None):
    group = group.copy()
    date_value, time_value = group_key if isinstance(group_key, tuple) else (None, None)
    if 'date' not in group.columns:
        group['date'] = date_value
    elif group['date'].isna().any():
        group['date'] = group['date'].fillna(date_value)
    if 'time' not in group.columns:
        group['time'] = time_value
    elif group['time'].isna().any():
        group['time'] = group['time'].fillna(time_value)

    sell_values = group.loc[group['code'] == 'sell', 'chg_pre'].values
    buy_values = group.loc[group['code'] == 'buy', 'chg_pre'].values
    if len(sell_values) == 0 or len(buy_values) == 0:
        return group

    sell_chg_pre = sell_values[0]
    buy_chg_pre = buy_values[0]
    difference = sell_chg_pre - buy_chg_pre
    if date_value is None and 'date' in group.columns:
        date_value = group['date'].iloc[0]
    if time_value is None and 'time' in group.columns:
        time_value = group['time'].iloc[0]
    new_row = pd.DataFrame({
        'id': [group['id'].max() + 1],
        'date': [date_value],
        'order_type': ['mean'],
        'time': [time_value],
        'code': ['differ'],
        'chg_pre': [difference]
    })
    return pd.concat([group, new_row], ignore_index=True)


def index_stra_detail(request, the_date='latest'):
    db = get_client(c_from='neo')
    t_yk = db.bt_paper_trade.minute_yk_first_v2_0
    t_alpha = db.bt_paper_trade.minute_alpha_first_v2_0
    

    if the_date == 'latest':
        the_date = next(t_alpha.find({}, {'_id': 0, 'date': 1}).sort([('date', -1), ]).limit(1)).get('date')
    else:
        the_date = next(t_alpha.find({'date': {'$lte': the_date}}, {'_id': 0, 'date': 1}).sort([('date', -1), ]).limit(1)).get('date')

    df1 = pd.DataFrame(t_alpha.find({'date': the_date}, {'_id': 0}))

    #fig_buy_a, fig_sell_a, fig_index_a = _return_df(df1, pro='阿尔法1号')
    df1['id'] = range(len(df1))
    df3 = pd.concat(
        [calculate_difference(group, group_key=key) for key, group in df1.groupby(['date', 'time'])],
        ignore_index=True,
    )
    df3['id'] = range(0, len(df3))
    fig_buy_a, fig_sell_a, fig_index_a = _return_df(df3, pro='阿尔法1号')


    df2 = pd.DataFrame(t_yk.find({'date': the_date}, {'_id': 0}))
    df2['id'] = range(len(df2))
    df4 = pd.concat(
        [calculate_difference(group, group_key=key) for key, group in df2.groupby(['date', 'time'])],
        ignore_index=True,
    )
    df4['id'] = range(0, len(df4))
    fig_buy_yk, fig_sell_yk, fig_index_yk = _return_df(df4, pro='屿阔1号')
    return render(request, 'trade_detail/index_stra.html',
                  {'fig_buy_a': fig_buy_a, 'fig_sell_a': fig_sell_a, 'fig_index_a': fig_index_a, 'fig_buy_yk': fig_buy_yk,
                   'fig_sell_yk': fig_sell_yk, 'fig_index_yk': fig_index_yk, 'trade_date': the_date})


def _plot_detail(ddf: pd.DataFrame, pro=None):
    """画正常账户"""
    df = ddf.loc[ddf.order_sum != 0, ['time', 'order_sum', 'curr_canuse_money', 'order_pct']].sort_values('time')
    df['time'] = df.time.apply(lambda x: x[:5])
    g1 = go.Scatter(x=df['time'], y=df['curr_canuse_money'], name='可用资金')
    g11 = go.Scatter(x=df['time'], y=df.order_pct.cumsum() * df.curr_canuse_money.max(), name='交易进度', )
    g2 = go.Scatter(x=df['time'], y=df['order_sum'], mode="markers", name='订单金额', xaxis='x', yaxis='y2',
                    marker={"color": df['order_sum'] * (-1), })
    fig = go.Figure(data=[g1, g2, g11],
                    layout={
                        'height': 1122,
                        "title": f"交易细节 ~ {pro}",
                        "font": {"size": 22, },
                        "yaxis": {"title": "账户可用资金 & 交易进度累计", },
                        "yaxis2": {"title": "订单金额（负买，正卖）", "side": "right", "overlaying": "y"},
                        "template": "presentation"
                    })
    return fig.to_html(full_html=False, include_plotlyjs=True)



def _plot_margin(ddf: pd.DataFrame, pro=None):
    """画股衍账户"""
    df = ddf.loc[ddf.order_sum != 0, ['time', 'order_sum', '保证金', '保证金占用率', 'order_pct']].sort_values('time')
    df['time'] = df.time.apply(lambda x: x[:5])
    my_money = format(df.iloc[-1]['保证金'] / 100000000, '.2f')
    last_margin = format(df.iloc[-1]['保证金占用率'], '.2%')

    df['time'] = df.time.apply(lambda x: x[:5])
    g1 = go.Scatter(x=df['time'], y=df['保证金占用率'] * 100, name='保证金比例')
    g11 = go.Scatter(x=df['time'], y=df.order_pct.cumsum() * 100, name='交易进度', )
    g2 = go.Scatter(x=df['time'], y=df['order_sum'], mode="markers", name='订单金额', xaxis='x', yaxis='y2',
                    marker={"color": df['order_sum'] * (-1), })
    fig = go.Figure(data=[g1, g2, g11],
                    layout={
                        'height': 1122,
                        "title": f"{pro}，最近保证金：{my_money}E，比例：{last_margin}",
                        "font": {"size": 22, },
                        "yaxis": {"title": "保证金比例 & 交易进度累计", "ticksuffix": "%", },
                        "yaxis2": {"title": "订单金额（负买，正卖）", "side": "right", "overlaying": "y"},
                        "template": "presentation"
                    })
    # fig.show()
    return fig.to_html(full_html=False, include_plotlyjs=True)
'''

def _plot_dma_detail(df: pd.DataFrame, txt: str):
    ddf = df.sort_values('time')
    # net_value_sum = ddf.order_value.sum() * (-1)
    g1 = go.Scatter(x=ddf['time'], y=ddf['net_sum'], name='累计净成交')
    # g11 = go.Scatter(x=ddf['time'], y=ddf.order_pct.cumsum() * ddf.order_value.max(), xaxis='x', yaxis='y2', name='交易进度')
    g2 = go.Scatter(x=ddf['time'], y=ddf['order_value'], mode="markers", name='订单金额', xaxis='x', yaxis='y2',
                    marker={"color": ddf['order_value'] * (-1), })
    
    fig = go.Figure(data=[g1, g2, ],
                    layout={
                        'height': 1122,
                        "title": f"交易细节 ~ {txt}",
                        "font": {"size": 22, },
                        "yaxis": {"title": "累计净成交金额", },
                        "yaxis2": {"title": "订单金额（负买，正卖）", "side": "right", "overlaying": "y"},
                        "template": "presentation"
                    })
    return fig.to_html(full_html=False, include_plotlyjs=True)

'''


def _plot_dma_detail(df: pd.DataFrame, txt: str):
    # 将数据按时间排序
    ddf = df.sort_values('time')

    # 创建图表中的两个数据序列
    g1 = go.Scatter(x=ddf['time'], y=ddf['net_sum'], name='累计净成交')
    g2 = go.Scatter(x=ddf['time'], y=ddf['order_value'], mode="markers", name='订单金额', xaxis='x', yaxis='y2',
                    marker={"color": ddf['order_value'] * (-1)})

    # 查找并标记14:30的时间点（直接使用字符串匹配）
    if '14:30' in ddf['time'].values:
        time_1430 = ddf[ddf['time'] == '14:30']['time'].iloc[0]
    else:
        time_1430 = None

    # 设置图表布局，添加14:30的垂直线标记
    fig = go.Figure(data=[g1, g2],
                    layout={
                        'height': 1122,
                        "title": f"交易细节 ~ {txt}",
                        "font": {"size": 22},
                        "xaxis": {"title": "时间"},
                        "yaxis": {"title": "累计净成交金额"},
                        "yaxis2": {"title": "订单金额（负买，正卖）", "side": "right", "overlaying": "y"},
                        "template": "presentation",
                        "shapes": [
                            {
                                'type': 'line',
                                'x0': time_1430,
                                'x1': time_1430,
                                'y0': 0,
                                'y1': 1,
                                'xref': 'x',
                                'yref': 'paper',
                                'line': {'color': 'red', 'width': 2, 'dash': 'dash'},
                            }
                        ] if time_1430 else []
                    })

    return fig.to_html(full_html=False, include_plotlyjs=True)


def trade_detail(request, the_date='latest'):
    
    db = get_client(c_from='neo')['trade_detail']
    t_ = db['alpha_first_margin']
    if the_date == 'latest':
        the_date = next(t_.find({}, {'_id': 0, 'date': 1}).sort([('date', -1), ]).limit(1)).get('date')
    else:
        the_date = next(t_.find({'date': {'$lte': the_date}}, {'_id': 0, 'date': 1}).sort([('date', -1), ]).limit(1)).get('date')
    # df_alpha_zx = pd.DataFrame(t_.find({'date': the_date}, {'_id': 0}))
    # if df_alpha_zx.empty:
    #     return render(request, 'trade_detail/index.html', {'trade_date': the_date + " 毛数据！！！"})

    # df_alpha_hx = pd.DataFrame(db['alpha_first_huaxi'].find({'date': the_date}, {'_id': 0}))
    df_alpha_df = pd.DataFrame(db['alpha_first_dongfang'].find({'date': the_date}, {'_id': 0}))
    # df_yk_cj = pd.DataFrame(db['yk_first_changjiang'].find({'date': the_date}, {'_id': 0}))

    alpha_margin = pd.DataFrame(db['alpha_first_margin'].find({'date': the_date}, {'_id': 0, 'order_no': 0}))
    dmz_zx = pd.DataFrame(db['dma_zx'].find({'委托日期': the_date},
                                            {'_id': 0, '委托编号': 0, '市场类型': 0, '错误信息': 0, '标的代码': 0, '标的简称': 0}))
    # alpha_margin = pd.DataFrame(db['alpha_first_margin'].find({'date': '2024-01-24'}, {'_id': 0, 'order_no': 0}))
    # %%
    context = {
        'trade_date': the_date,
        # 'alpha_zx': _plot_detail(df_alpha_zx, '阿尔法1号(中信)'),
        # 'alpha_hx': _plot_detail(df_alpha_hx, '阿尔法1号(华西)'),
        'dmz_zx': _plot_dma_detail(dmz_zx, '阿尔法1号(股衍交割单)'),
        'alpha_margin': _plot_margin(alpha_margin, '阿尔法1号(景天交割单)'),
        'alpha_df': _plot_detail(df_alpha_df, '阿尔法1号(东方)'),
        # 'yk_cj': _plot_detail(df_yk_cj, '屿阔1号(长江)'),
    }
    return render(request, 'trade_detail/index.html', context)


