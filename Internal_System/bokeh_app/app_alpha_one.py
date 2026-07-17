# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: vis_alpha_one.py
@time: 2023/5/25 17:47
说明:
"""
import sys

sys.path.append("D:/Neo/WorkPlace/ShuiDQReport/")

import pandas as pd
import holoviews as hv
from holoviews import opts
# import hvplot.pandas  # noqa
from bokeh.io import curdoc
from bokeh.layouts import layout
from bokeh.models import Slider, Button

from Datas.load_data import LoadData
from Datas import stat

renderer = hv.renderer('bokeh').instance(mode='server')


def plot_dyn(end_index):
    df_plot = df_data.loc[:end_index].copy()
    df_plot["date"] = pd.to_datetime(df_plot.date)
    # 增加回撤指标
    df_plot = stat.stat_max(df_plot, col='net_value5')
    df_plot['back'] = df_plot['net_value5'] / df_plot['max_value'] - 1
    df_plot['back_per'] = (df_plot.back * 100).round(2)
    the_date = df_plot.loc[df_plot.back.idxmin(), 'date']
    the_pos = df_plot.loc[df_plot.back.idxmin(), 'net_value5']
    point_max_back = hv.Points(pd.DataFrame(dict(x=[the_date, ], y=[the_pos, ], ))).opts(size=6)
    back_text = '历史最大回撤点\n日期：{}，幅度：{:.2%}'.format(str(the_date)[:10], df_plot.back.min())
    text_max_back = hv.Text(the_date, the_pos, text=back_text, valign='top', halign='left')
    back_dim = hv.Dimension('back_per', label='回撤比列', unit='%')
    back_spikes = hv.Spikes(df_plot, 'date', back_dim).opts(xaxis=None, color='grey')

    # 策略年化收益率
    stra_chg = df_plot.loc[end_index]['net_value5'] - 1
    stra_annual = df_plot.loc[end_index].net_value5 ** (250 / df_plot.net_value5.size) - 1
    stra_std = 20 ** 0.5 * df_plot.chg5.std()
    stra_sharp = 365 ** 0.5 * df_plot.chg5.mean() / df_plot.chg5.std()
    stra_title = '【{} - {}】总收益：{:.2%}，年化收益：{:.2%}，波动率：{:.2%}，年化夏普率：{:.2f}'.format(
        str(df_plot.loc[0]['date'])[:10], str(df_plot.loc[end_index]['date'])[:10],
        stra_chg, stra_annual, stra_std, stra_sharp)
    curve = hv.Curve(df_plot, 'date', 'net_value5')
    x_md = df_plot.date.median()
    y_md = df_plot.loc[0].net_value5
    text = hv.Text(x_md, y_md, df_plot.loc[end_index].date.strftime('%Y-%m'), fontsize=30).opts(
        text_font_size='55pt', text_color='lightgray'
    )

    turn_title = "换手率(标红) & 回撤(标灰) 指标 --->>> 平均单边换手率 {:.2%}".format(df_plot.stra_turnover.mean())
    df_plot['stra_turnover_per'] = (df_plot.stra_turnover * 100).round(2)
    turnover_dim = hv.Dimension('stra_turnover_per', label='换手率', unit='%')
    turn_spikes = hv.Spikes(df_plot, 'date', turnover_dim).opts(
        xaxis=None, color='purple', title=turn_title, ylabel="换手率 & 回撤（%）")
    lay1 = curve * text * point_max_back * text_max_back
    lay2 = back_spikes * turn_spikes

    return (lay1 + lay2).opts(
        opts.Spikes(framewise=True, width=ld.width3, height=200, line_width=0.25, tools=['hover']),
        opts.Curve(framewise=True, height=ld.high, width=ld.width3, tools=['hover'], title=stra_title),
    ).cols(1)


def modify_doc(doc):
    hvplot = renderer.get_plot(dmap, doc)

    def animate_update():
        ind = slider.value + 5
        if ind > end:
            ind = start
        slider.value = ind

    def slider_update(attrname, old, new):
        # print("in slider_update ---->>>>", attrname, old)
        stream.event(end_index=new)

    start, end = df_data.index.values[0], df_data.index.values[-1]
    slider = Slider(start=start, end=end, value=start, step=1, title="策略运行天数", width=ld.width3, )
    slider.on_change('value', slider_update)

    callback_id = None

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

    plot = layout([[hvplot.state], [slider, button]], sizing_mode='fixed')

    doc.add_root(plot)
    return doc


ld = LoadData()
df_data = ld.get_bt_strategy(stra_name="alpha_one")

stream = hv.streams.Stream.define('策略运行天数', end_index=df_data.index.values[0])()
dmap = hv.DynamicMap(plot_dyn, streams=[stream])

doc = modify_doc(curdoc())
doc.title = '策略净值走势动态展示'
