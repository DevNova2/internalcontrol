# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: app_trade_detail_sell.py
@time: 2023/8/3 16:30
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
from bokeh.models import DatePicker
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

    df1 = df_data.loc[the_date].copy()
    df1.set_index('成交时间', inplace=True)
    df1['交易时间'] = pd.to_datetime(df1['Date Time'])
    df1.loc['13:00:00':, '交易时间'] = df1.loc['13:00:00':]['交易时间'] + timedelta(minutes=-90)
    df1.set_index('交易时间', inplace=True)
    df1['资金本次余额'] = df1['资金本次余额'] / 10000
    df1['发生金额'] = df1['发生金额'] / 10000
    p1 = hv.Scatter(df1, '交易时间', '资金本次余额', label='账户可用资金').opts(color='red', )
    p2 = hv.Scatter(df1, '交易时间', '发生金额', label='买卖金额').opts(color='blue', )

    df3_ = df_detail.loc[the_date][['time', 'code', 'money', 'chg', 'trade', 'Date Time']].copy()
    df3_.set_index('time', inplace=True)
    df3_['交易时间'] = pd.to_datetime(df3_['Date Time'])
    df3_.loc['13:00:00':, '交易时间'] = df3_.loc['13:00:00':]['交易时间'] + timedelta(minutes=-90)
    df3_.set_index('trade', inplace=True)

    df_sell = df3_.loc[2][['code', 'money', 'chg', '交易时间']].copy()
    df_sell.sort_values('交易时间', inplace=True)
    df_sell.set_index('code', inplace=True)
    df_sell_avg_mean = df_sell.groupby('交易时间').apply(_cal_chg_avg_and_mean)
    line_sell_mean = hv.Curve(df_sell_avg_mean, '交易时间', 'chg_mean', label='换出票平均涨跌').opts(framewise=True, color='red', line_width=3)
    line_sell_avg = hv.Curve(df_sell_avg_mean, '交易时间', 'chg_avg', label='换出票加权涨跌').opts(framewise=True, color='blue', line_width=3)

    curve_dict_sell = {code: hv.Curve(df_sell.loc[code], '交易时间', 'chg', label=code) for code in df_sell.index.unique().tolist()}
    ndoverlay_sell = (hv.NdOverlay(curve_dict_sell, kdims='codes') * line_sell_mean * line_sell_avg).opts(
        opts.NdOverlay(framewise=False, height=int(ld.high2 * 1.4), width=ld.width3, legend_position='right', gridstyle=GRID_STYLE,
                       title="换出 分钟涨跌幅，交易日：{}".format(the_date), ),
    )

    return ((p1 * p2).relabel("整体趋势，交易日：{}".format(the_date)) + ndoverlay_sell).opts(
        opts.Curve(framewise=True, tools=['hover'], show_grid=True, gridstyle=GRID_STYLE, autorange='y', yformatter=formatter),
        opts.Scatter(framewise=True, tools=['hover'], jitter=0.2, alpha=0.5, size=4, show_grid=True, gridstyle=GRID_STYLE),
        opts.Overlay(framewise=True, height=int(ld.high2 * 1.4), width=ld.width3, legend_position='right', gridstyle=GRID_STYLE, ),
    ).cols(1)


def handler_date_picker(attr, old, new):
    global stream
    print(f"------->>>>>>> old={old},day_new={new}")
    stream.event(the_date=new)


def modify_doc(doc, default_date, min_date, max_date):
    hvplot = renderer.get_plot(dmap, doc)

    date_picker = DatePicker(title="选择交易日期", value=default_date, min_date=min_date, max_date=max_date)
    date_picker.on_change("value", handler_date_picker)

    plot = layout([[date_picker, ], [hvplot.state], ], sizing_mode='fixed')

    doc.add_root(plot)
    return doc


# if __name__ == '__main__':
ld = LoadData()
df_data = ld.load_latest_month_statement_of_account(start_date='20230701')
df_data['time'] = df_data['成交时间'].apply(lambda x: x[:6] + '00')
df_data = df_data[['date', '成交时间', 'time', 'Date Time', '资金本次余额', '发生金额']].copy()
default_day = df_data.date.max()
min_day = df_data.date.min()
df_data.set_index('date', inplace=True)
df_index, df_detail = ld.load_stra_index_detail(start_date='2023-07-01')

stream = hv.streams.Stream.define('交易日', the_date=default_day)()
dmap = hv.DynamicMap(plot_dyn, streams=[stream])

my_doc = modify_doc(curdoc(), default_day, min_day, default_day)

my_doc.title = '换出 - 交易细节静态展示'
