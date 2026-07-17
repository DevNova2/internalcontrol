# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: app_trade_detail.py
@time: 2023/6/29 11:09
说明:
"""

import sys
import time

sys.path.append("D:/Neo/WorkPlace/ShuiDQReport/")
from datetime import datetime, timedelta
import pandas as pd
import holoviews as hv
from holoviews import opts
from bokeh.io import curdoc
from bokeh.layouts import layout
from bokeh.models import Button, DatePicker, DatetimeRangeSlider
from Datas.load_data import LoadData

renderer = hv.renderer('bokeh').instance(mode='server')


def update_plot_data(the_date):
    global df_data
    df = df_data[df_data.date == the_date].copy()
    df['trade'] = 0
    df.set_index('成交时间', inplace=True)
    df.sort_index(inplace=True)

    sell_list = df[df['股份余额'] == 0].code.unique().tolist()  # 有可能为空，那么对应的换入也为空
    tmp_list = df[~(df.code.isin(sell_list))].code.unique().tolist()
    buy_list = tmp_list[:len(sell_list)]
    # print(sell_list, buy_list)
    df.loc[df.code.isin(sell_list), 'trade'] = 2
    df.loc[df.code.isin(buy_list), 'trade'] = 1
    return df


def plot_dyn(end_index):
    global df_plot
    df = df_plot.loc[:end_index].copy()
    df['交易时间'] = pd.to_datetime(df['Date Time'])
    df.loc['13:00:00':, '交易时间'] = df.loc['13:00:00':]['交易时间'] + timedelta(minutes=-90)
    df1 = df[['交易时间', '资金本次余额', '发生金额', '成交金额']].copy()
    df1.dropna(inplace=True)
    df1.set_index('交易时间', inplace=True)
    df1 = df1 / 10000

    p1 = hv.Scatter(df1, '交易时间', '资金本次余额', label='账户可用资金').opts(color='red')
    p2 = hv.Scatter(df1, '交易时间', '发生金额', label='买卖金额').opts(color='blue')
    # p3 = hv.Scatter(df1, '交易时间', '成交金额', label='订单大小').opts(color='green')

    df2 = df[['交易时间', 'code', '成交价格', '股份余额', 'trade']].copy()
    df2.dropna(inplace=True)
    df2 = df2[df2.trade > 0].copy()
    df2['持仓市值'] = (df2['成交价格'] * df2['股份余额']) / 10000
    df2.set_index('交易时间', inplace=True)

    curve_dict = {code: hv.Curve(df2[df2.code == code], '交易时间', '持仓市值', label=code) for code in df2.code.unique().tolist()}
    ndoverlay = hv.NdOverlay(curve_dict, kdims='codes')

    s3 = df2.index.value_counts()
    df3 = s3.reset_index()
    df3.sort_values('交易时间', inplace=True)
    back_spikes = hv.Spikes(df3, '交易时间', 'count')
    text = hv.Text(0.5, 0.5, end_index, fontsize=30).opts(text_font_size='55pt', text_color='lightgray')

    gridstyle = {'grid_line_dash': [6, 4], 'grid_line_width': 1.5}
    return ((p1 * p2).relabel("整体趋势") + ndoverlay.relabel("个股市值") + back_spikes.relabel("订单数量") + text.relabel("最后订单时间")).opts(
        opts.Curve(framewise=True, tools=['hover'], show_grid=True),
        opts.Scatter(framewise=True, tools=['hover'], jitter=0.2, alpha=0.5, size=4, show_grid=True),
        opts.Overlay(framewise=True, height=ld.high, width=ld.width_h, legend_position='top_left', gridstyle=gridstyle),
        opts.NdOverlay(framewise=True, height=ld.high, width=ld.width_h, legend_position='right', gridstyle=gridstyle),
        opts.Spikes(framewise=True, width=ld.width_h, height=200, tools=['hover'], cmap='Reds'),
        opts.Text(framewise=True, width=ld.width_h, height=200, xaxis=None, yaxis=None),
    ).cols(2)


def modify_doc(doc, default_date, min_date, max_date):
    global df_plot, trade_times
    hvplot = renderer.get_plot(dmap, doc)
    time_min, time_max = trade_times[0], trade_times[-1]

    def handler_date_picker(attr, old, new):
        global df_plot, trade_times
        df_plot = update_plot_data(new)
        if df_plot.empty:
            datetime_range_slider.title = "注意，这天没有交易！！！"
            return
        datetime_range_slider.title = "点击右边【► Play】开始自动运转 --->>>"
        # print(df_plot)
        trade_times = df_plot['Date Time'].unique().tolist()
        datetime_range_slider.start = trade_times[0]
        datetime_range_slider.end = trade_times[-1]
        datetime_range_slider.value = (trade_times[0], trade_times[0])

        stream.event(end_index=df_plot.index.unique().tolist()[-1])

    date_picker = DatePicker(title="选择交易日期", value=default_date, min_date=min_date, max_date=max_date)
    date_picker.on_change("value", handler_date_picker)

    def handler_slider_update(attrname, old, new):
        current_time = str(datetime.fromtimestamp((new[1] - 8 * 3600 * 1000) / 1000))
        # print(f'slider 更新了，当前时间是：{current_time},---{current_time[-8:]}')
        stream.event(end_index=current_time[-8:])

    datetime_range_slider = DatetimeRangeSlider(value=(time_min, time_min), start=time_min, end=time_max,
                                                width=ld.width2, format='%Y-%m-%d %H:%M:%S',
                                                step=1000, title="点击右边【► Play】开始自动运转 --->>>"
                                                )
    datetime_range_slider.on_change('value', handler_slider_update)

    def animate_update():
        current_values = datetime_range_slider.value
        current_time = str(datetime.fromtimestamp((current_values[1] - 8 * 3600 * 1000) / 1000))
        if current_time not in trade_times:
            print('not int trade_times，将跳转到下一个交易时间点')
            tmp_l = trade_times + [current_time, ]
            tmp_l.sort()
            current_time = tmp_l[tmp_l.index(current_time) - 1]
        current_index = trade_times.index(current_time)
        if current_index == len(trade_times) - 1:
            next_time = trade_times[0]
            time.sleep(10)
        else:
            next_time = trade_times[current_index + 1]
        datetime_range_slider.value = (trade_times[0], next_time)

    def animate():
        global callback_id
        if button.label == '► Play':
            button.label = '❚❚ Pause'
            callback_id = doc.add_periodic_callback(animate_update, 50)
        else:
            button.label = '► Play'
            doc.remove_periodic_callback(callback_id)

    button = Button(label='► Play', width=60)
    button.on_click(animate)

    plot = layout([[date_picker, datetime_range_slider, button], [hvplot.state], ], sizing_mode='fixed')

    doc.add_root(plot)
    return doc


# if __name__ == '__main__':
callback_id = None
ld = LoadData()
df_data = ld.load_latest_month_statement_of_account(start_date='20230601')
default_day = df_data.date.max()
min_day = df_data.date.min()
df_plot = update_plot_data(default_day)
trade_times = df_plot['Date Time'].unique().tolist()

stream = hv.streams.Stream.define('交易时间节点', end_index=df_plot.index.unique().tolist()[-1])()
dmap = hv.DynamicMap(plot_dyn, streams=[stream])

my_doc = modify_doc(curdoc(), default_day, min_day, default_day)
my_doc.title = '交易细节动态展示'
