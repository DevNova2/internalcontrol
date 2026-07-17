# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: app_trade_detail_yk_one.py
@time: 2023/8/18 14:38
说明:
"""
import sys

sys.path.append("D:/Neo/WorkPlace/ShuiDQReport/")

import numpy as np
from datetime import timedelta
import pandas as pd
import holoviews as hv
from holoviews import opts
from bokeh.io import curdoc
from bokeh.layouts import layout
from bokeh.models import DatePicker, Toggle
from Datas.load_data import LoadData

renderer = hv.renderer('bokeh').instance(mode='server')
GRID_STYLE = {'grid_line_dash': [6, 4], 'grid_line_width': 1.5}


def formatter(value):
    return str(value)[:3] + '%'


def _cal_chg_avg_and_mean(df):
    stra_chg_mean = df.chg.mean()
    money_sum = df.money.sum()
    if money_sum > 0:
        stra_chg_avg = np.sum(df.chg * df.money) / money_sum
    else:
        stra_chg_avg = stra_chg_mean
    return pd.Series(data={'chg_mean': stra_chg_mean, 'chg_avg': stra_chg_avg})


def plot_dyn(the_date):
    global df_data, df_detail
    start_time = '09:30'

    df = df_detail.loc[the_date].copy()
    tmp_list = []
    for i in range(3):
        tmp_list.append((start_time, np.nan, 0, i))
    df = pd.concat((pd.DataFrame(tmp_list, columns=['time', 'code', 'chg', 'trade']), df))

    time_list = df.time.unique().tolist()
    xtick_all = [(t, time_list[t][:5]) for t in range(0, len(time_list))]
    xtick = [(t, time_list[t][:5]) for t in range(0, len(time_list), 6)]

    s_all = df.groupby('time', as_index=False)['chg'].mean()
    df_buy = df[df.trade == 1].copy()
    s_buy = df_buy.groupby('time', as_index=False)['chg'].mean()
    df_sell = df[df.trade == 2].copy()
    s_sell = df_sell.groupby('time', as_index=False)['chg'].mean()
    line_all_mean = hv.Curve(s_all[['chg', ]], label='组合平均涨跌').opts(framewise=True, color='gray', xticks=xtick, line_width=3)
    line_buy_mean = hv.Curve(s_buy[['chg', ]], label='换入平均涨跌').opts(framewise=True, color='red', xticks=xtick, )
    line_sell_mean = hv.Curve(s_sell[['chg', ]], label='换出平均涨跌').opts(framewise=True, color='blue', xticks=xtick, )
    lay_mean = line_all_mean * line_sell_mean * line_buy_mean

    df1 = df_data.loc[the_date].copy()
    df_xtick = pd.DataFrame(data=xtick_all, columns=['times', 'time'])
    df1 = pd.merge(df_xtick, df1, on='time')
    df1.set_index('times', inplace=True)
    p1 = hv.Scatter(df1[['资金本次余额', ]], label='账户可用资金').opts(framewise=True, color='red', xticks=xtick, )
    p2 = hv.Scatter(df1[['发生金额', ]], label='买卖金额').opts(framewise=True, color='blue', xticks=xtick, )

    df_sell.dropna(inplace=True)
    df_sell.set_index('code', inplace=True)
    curve_dict_sell = {code: hv.Curve(df_sell.loc[code][['chg']].reset_index(drop=True), label=code) for code in df_sell.index.unique().tolist()}
    ndoverlay_sell = (hv.NdOverlay(curve_dict_sell, kdims='codes')).relabel("换出 分钟涨跌幅，交易日：{}".format(the_date))

    df_buy.dropna(inplace=True)
    df_buy.set_index('code', inplace=True)
    curve_dict_buy = {code: hv.Curve(df_buy.loc[code][['chg']].reset_index(drop=True), label=code) for code in df_buy.index.unique().tolist()}
    ndoverlay_buy = (hv.NdOverlay(curve_dict_buy, kdims='codes')).relabel("换入 分钟涨跌幅，交易日：{}".format(the_date))

    return ((p1 * p2).relabel("整体趋势，交易日：{}".format(the_date)) + ndoverlay_sell + lay_mean.relabel(
        "指数，交易日：{}".format(the_date)) + ndoverlay_buy).opts(
        opts.Curve(framewise=True, tools=['hover'], show_grid=True, gridstyle=GRID_STYLE, autorange='y', yformatter=formatter, xticks=xtick,
                   xrotation=90, ),
        opts.Scatter(framewise=True, tools=['hover'], jitter=0.2, alpha=0.5, size=4, show_grid=True, gridstyle=GRID_STYLE, xticks=xtick,
                     xrotation=90, ),
        opts.Overlay(framewise=True, height=int(ld.high2 * 1.4), width=ld.width_h, legend_position='top_right', gridstyle=GRID_STYLE,
                     xticks=xtick, xrotation=90, shared_axes=False),
        opts.NdOverlay(framewise=True, height=int(ld.high2 * 1.4), width=ld.width_h, legend_position='top_right', gridstyle=GRID_STYLE,
                       xticks=xtick, xrotation=90, shared_axes=False),
    ).cols(2)


def handler_date_picker(attr, old, new):
    global stream
    print(f"------->>>>>>> old={old},day_new={new}")
    stream.event(the_date=new)


def modify_doc(doc, default_date, min_date, max_date):
    hvplot = renderer.get_plot(dmap, doc)

    date_picker = DatePicker(title="选择交易日期", value=default_date, min_date=min_date, max_date=max_date)
    date_picker.on_change("value", handler_date_picker)

    toggle = Toggle(label="屿阔精选一号", button_type="danger")

    plot = layout([[date_picker, ],
                   [toggle, ],
                   [hvplot.state],
                   ], sizing_mode='fixed')

    doc.add_root(plot)
    return doc


ld = LoadData()
df_detail, min_day = ld.load_pro_detail(pro='YK1')
df_detail['code'] = df_detail.code.apply(lambda x: x[:6])
df_detail['time'] = df_detail.time.apply(lambda x: x[:5])
df_detail = df_detail[['date', 'time', 'code', 'chg', 'trade']].copy()
df_detail.set_index('date', inplace=True)

df_data = ld.load_yk_trade_detail()
df_data['Date Time'] = df_data.date + ' ' + df_data['成交时间']
df_data['交易时间'] = pd.to_datetime(df_data['Date Time']) + timedelta(minutes=1)
df_data['time'] = df_data['交易时间'].astype(str).str[-8:-3]
df_data['date'] = df_data['交易时间'].astype(str).str[:10]
df_data = df_data[['date', 'time', '剩余金额', '发生金额']].copy()
df_data['资金本次余额'] = abs(df_data['剩余金额'].astype('float')) / 10000
df_data['发生金额'] = df_data['发生金额'].astype('float') / 10000
df_data.set_index('date', inplace=True)
default_day = df_data.index.max()

stream = hv.streams.Stream.define('交易日', the_date=default_day)()
dmap = hv.DynamicMap(plot_dyn, streams=[stream])

my_doc = modify_doc(curdoc(), default_day, min_day, default_day)
my_doc.title = '屿阔精选一号 - 交易细节'
