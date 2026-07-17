# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: vis_layer.py
@time: 2023/5/29 15:07
说明:
"""
import datetime
import math
import multiprocessing as mp
import pandas as pd

from ShuiDQReport.settings import BASE_DIR
from Datas.load_data import LoadData
from Datas import stat


def proc_plot(chg_df, factor, date_s='2022-01-01', date_e='2022-12-31'):
    pld = LoadData()
    chg = chg_df.copy()
    df_factor = pld.get_layer_factor(factor=factor, date_s=date_s, date_e=date_e)
    df_groups = stat.layer_backtest(df_factor, chg, col=factor)
    new_cols = dict(enumerate([f'第{i + 1}组' for i in df_groups.columns.values.tolist()]))
    df_groups.rename(columns=new_cols, inplace=True)
    df_plot = (df_groups + 1).cumprod()
    plot_cols = df_plot.columns.values.tolist()
    df_plot['date'] = pd.to_datetime(df_plot.index)
    df_plot.reset_index(inplace=True, drop=True)

    overlay = hv.NdOverlay({col: hv.Curve(df_plot, 'date', col).opts(
        shared_axes=False, tools=['hover']) for col in plot_cols})

    print(overlay)
    return overlay
    # hv.save(overlay, inc_dir + "inc_" + factor + "_net_value_all.html")


def vis_key_factors(ld):
    inc_dir = str(BASE_DIR) + "/layer_bt/templates/layer_bt/"
    # ld = LoadData()
    the_date, fac_dict = ld.get_factors_weights()
    factors = ['F1', 'mv_vol',
               # 'F_C'
               ] + list(fac_dict.keys())
    # print(factors)
    today = datetime.date.fromisoformat(the_date)
    start_day = str(datetime.date(today.year - 3, today.month, today.day))

    days = [start_day, the_date]
    # print(days)

    df_chg = ld.get_dates_chg(days[0], days[-1])

    layouts = []

    pool = mp.Pool(math.ceil(mp.cpu_count() / 2))
    for fac in factors:
        result = pool.apply_async(proc_plot, args=(df_chg, fac, days[0], days[-1]),
                                  error_callback=throw_exception)
        layouts.append((result, fac))
    pool.close()
    pool.join()
    layout = hv.Layout()
    for lay_tup in layouts:
        overlay = lay_tup[0].get()
        # 样式在子进程中设置不起作用，放这里来
        overlay.opts(legend_position='top', width=ld.width2, height=ld.high, shared_axes=False,
                     show_grid=True, xlabel="日期【{} - {}】".format(days[0], days[-1]), ylabel="分组净值走势",
                     title="{} 单调性检测(近3年)".format(lay_tup[1]))
        layout = layout + overlay

    layout.opts(shared_axes=False).cols(1)

    hv.save(layout, inc_dir + "inc_net_value_all.html")


if __name__ == '__main__':
    ts = datetime.datetime.now()

    te = datetime.datetime.now()
    print(te - ts)
