# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: vis_F1.py
@time: 2023/5/24 11:02
说明:
"""
import numpy as np
import pandas as pd
import hvplot
import hvplot.pandas  # noqa

import holoviews as hv
from holoviews.util.transform import dim
from holoviews import opts

from ShuiDQReport.settings import BASE_DIR
from Datas.load_data import LoadData

pd.options.plotting.backend = 'holoviews'
hv.extension('bokeh')


class FactorView(object):
    """单因子 行业、市值 单调性检查通用类"""

    def __init__(self, ld_data, factor=None):
        if factor is None:
            raise Exception("没有指定factor，怎么搞？")

        self.inc_dir = str(BASE_DIR) + "/mult_factor/templates/mult_factor/" + factor + "/"
        self.factor = factor

        self.ld = ld_data

        print(self.factor)

    def html_chg_by_group(self):
        df = self.ld.get_chg_factor(factor=self.factor)
        df.reset_index(inplace=True, drop=True)
        group_num = 50
        each_group = df.shape[0] // group_num
        df['bench_chg'] = df.chg.mean()
        for i in range(0, group_num):
            df.loc[i * each_group:((i + 1) * each_group) - 1, 'gro'] = i + 1
            ddf = df.loc[i * each_group:((i + 1) * each_group) - 1]

            df.loc[i * each_group:((i + 1) * each_group) - 1, 'gro_up_count'] = len(ddf[ddf.chg >= 0])
            df.loc[i * each_group:((i + 1) * each_group) - 1, 'gro_down_count'] = len(ddf[ddf.chg < 0])
            gro_mean_chg = ddf.chg.mean()
            df.loc[i * each_group:((i + 1) * each_group) - 1, 'gro_mean_chg'] = gro_mean_chg
            # gro_std = 20 ** 0.5 * ddf.chg.std()
            # df.loc[i * each_group:((i + 1) * each_group) - 1, 'gro_sharp'] = 365 ** 0.5 * gro_mean_chg / gro_std
        df.dropna(inplace=True)
        df_plot = df[~(df.duplicated(subset=['gro', ], keep='last'))].copy()
        df_plot.reset_index(inplace=True, drop=True)
        bars = df_plot.hvplot.bar(x='gro', y=['gro_up_count', 'gro_down_count'], color=["red", "green"],
                                  ylabel="", xlabel="分组", width=self.ld.width1, rot=90,
                                  title="每组({}只)股票的涨跌数量，因子日期：{}，收益日期：{}".format(each_group,
                                                                                                  self.ld.the_last_date,
                                                                                                  self.ld.the_date),
                                  stacked=True, legend="top_right", )
        df_plot['gro_mean_chg_per'] = (df_plot.gro_mean_chg * 100).round(2)
        df_plot['bench_chg_per'] = (df_plot.bench_chg * 100).round(2)
        overlay = hv.NdOverlay({interp: hv.Curve(df_plot, 'gro', interp).opts(tools=['hover'])
                                for interp in ['gro_mean_chg_per', 'bench_chg_per']})
        overlay.opts(legend_position='top_right', width=self.ld.width1, show_grid=True, xlabel="分组", ylabel="涨跌幅(%)",
                     title="每组平均涨跌幅(%)、基准涨跌幅(%)")

        lay = bars + overlay
        lay.opts().cols(2)
        print(lay)
        hv.save(lay, self.inc_dir + "inc_" + self.factor + "_chg.html")

    def html_inds_and_cap(self):
        df = self.ld.get_about_factor(factor=self.factor)
        group_num = 50
        each_group = df.shape[0] // group_num
        for i in range(0, group_num):
            df.loc[i * each_group:((i + 1) * each_group) - 1, 'gro'] = i + 1
            count = df.loc[i * each_group:((i + 1) * each_group) - 1].ind.unique().size
            df.loc[i * each_group:((i + 1) * each_group) - 1, 'ind_count'] = count
        df.dropna(inplace=True)

        df_ind = df[~(df.duplicated(subset=['gro', 'ind_count'], keep='last'))][['gro', 'ind_count']]
        bar_ind = hv.Bars(df_ind).opts(
            xlabel="按 " + self.factor + " -->>分 {} 组，每组 {} 只票".format(group_num, each_group),
            ylabel="每组行业数", title="复合因子：{}，每组行业暴露度".format(self.factor))
        df_cap_median = df.groupby('gro').apply(lambda d: d.market_cap.median())
        df_cap_median = df_cap_median.to_frame(name="中位数")
        area = df_cap_median.hvplot.bar()

        df_cap_mean = df.groupby('gro').apply(lambda d: d.market_cap.mean())
        df_cap_mean = df_cap_mean.to_frame(name="平均值")
        scatter = df_cap_mean.hvplot.scatter(color='red')

        title = "复合因子：{}，市值规模暴露度 -->>分 {} 组，每组 {} 只票".format(self.factor, group_num, each_group)
        boxwhisker1 = hv.BoxWhisker(df, ('gro', '分组'), ('market_cap', '市值规模（亿）'), label=title)
        violin = hv.Violin(df, ('gro', '分组'), ('log_market_cap', '市值规模（亿）取对数'),
                           label=title + "（取对数）")

        layout = bar_ind + (area * scatter) + boxwhisker1 + violin
        layout.opts(
            opts.Overlay(xlabel="各分组 市值 中位数 & 平均值", ylabel="市值规模暴露度", show_legend=True,
                         multiple_legends=True, legend_position="top_left",
                         title="复合因子：{}，各分组暴露度 --->> 市值 中位数 & 平均值 ".format(self.factor),
                         shared_axes=False),
            opts.Bars(height=int(self.ld.high / 2), width=self.ld.width2, tools=['hover'], shared_axes=False),
            opts.Violin(height=self.ld.high, width=self.ld.width2, violin_fill_color=dim('gro').str(), tools=['hover']),
            opts.BoxWhisker(height=self.ld.high, width=self.ld.width2, tools=['hover'], shared_axes=False)
        ).cols(1)

        print(layout)
        hv.save(layout, self.inc_dir + "inc_" + self.factor + "_inds.html")


if __name__ == '__main__':
    ld = LoadData()
    factors = ['F1', 'mv_vol', 'F_C']
    for factor in factors:
        print("生成 {} 相关数据".format(factor))
        f1 = FactorView(ld_data=ld, factor=factor)
        f1.html_inds_and_cap()
        f1.html_chg_by_group()
