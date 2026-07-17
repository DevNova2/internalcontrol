# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: vis_stat.py
@time: 2023/6/1 17:00
说明:每日收盘后统计日、周、月频 涨跌幅数据
"""
import numpy as np
import pandas as pd
import panel as pn
import hvplot.pandas  # noqa

import holoviews as hv

from ShuiDQReport.settings import BASE_DIR
from Utils.utils import get_week_month_date
from layer_bt.load_data import LoadData
import warnings

warnings.filterwarnings('ignore', category=FutureWarning)
pd.options.plotting.backend = 'holoviews'
hv.extension('bokeh')
pn.extension()


class StatisticView(object):
    def __init__(self):
        self.inc_dir = str(BASE_DIR) + "/layer_bt/templates/statistic/"

        self.ld = LoadData()
        self.df_yesterday = self.ld.get_pre_cap_chg()
        self.df_today = self.ld.get_today_chg()

    def __html_cap(self, df, daily=True, des=None):
        df_cap = df.sort_values('mkt_cap_ard', ascending=False)
        df_cap.reset_index(inplace=True, drop=True)
        group_num = 10
        each_group = df_cap.shape[0] // group_num
        for i in range(0, group_num):
            df_cap.loc[i * each_group:((i + 1) * each_group) - 1, 'gro'] = i + 1
            ddf = df_cap.loc[i * each_group:((i + 1) * each_group) - 1]
            gro_mean_pct_chg = ddf.pct_chg.mean()
            df_cap.loc[i * each_group:((i + 1) * each_group) - 1, 'gro_mean_pct_chg'] = gro_mean_pct_chg
        df_cap.dropna(inplace=True)
        df_cap = df_cap[~(df_cap.duplicated(subset=['gro', ], keep='last'))].copy()
        df_cap.reset_index(inplace=True, drop=True)
        df_cap['gro_mean_pct_chg_per'] = df_cap.gro_mean_pct_chg.round(4) * 100
        df_cap['color'] = np.sign(df_cap['gro_mean_pct_chg'].tolist())
        df_cap['color'].replace([1, -1], ['red', 'blue'], inplace=True)
        if daily:
            title = "交易日：{} 市值分组平均涨跌幅".format(df.iloc[0].date)
        else:
            title = "交易区间：{} -- {}（{}）， 市值分组平均涨跌幅".format(df.iloc[0].date_s, df.iloc[0].date_e, des)
        bar_cap = df_cap.hvplot.bar(x="gro", y="gro_mean_pct_chg_per", width=self.ld.width1, c="color", shared_axes=False, yformatter='%.1f%%',
                                    xlabel="按市值从大到小分组", ylabel="每组平均涨跌幅", title=title)
        return bar_cap

    def __html_pct_chg(self, df, daily=True, des=None):
        df_pct_chg = df.sort_values('pct_chg')
        df_pct_chg.reset_index(inplace=True, drop=True)
        df_pct_chg['pct_chg_per'] = df_pct_chg.pct_chg.round(4) * 100
        if daily:
            bins = list(np.arange(-20.5, 20.5, 1))
            bins.append(20.5)
            df_pct_chg['pct_chg_range'] = pd.cut(x=df_pct_chg["pct_chg_per"], bins=bins, labels=list(range(-20, 21, 1)))
            title = "交易日：{} 涨跌幅分布".format(df.iloc[0].date)
        else:
            bins = list(np.arange(-30.5, 30.5, 1))
            bins.append(30.5)
            df_pct_chg['pct_chg_range'] = pd.cut(x=df_pct_chg["pct_chg_per"], bins=bins, labels=list(range(-30, 31, 1)))
            title = "交易区间：{} -- {}（{}）， 市值分组平均涨跌幅".format(df.iloc[0].date_s, df.iloc[0].date_e, des)
        a = df_pct_chg["pct_chg_range"].value_counts(sort=False)
        df_plot = pd.DataFrame({'涨跌幅区间': a.index, "股票数量": a.values})
        df_plot['color'] = np.sign(df_plot['涨跌幅区间'].tolist())
        df_plot['color'].replace([1, 0, -1], ['red', 'grey', 'blue'], inplace=True)
        bar_pct_chg = df_plot.hvplot.bar(x="涨跌幅区间", y="股票数量", width=self.ld.width_h, c="color", rot=90,
                                         shared_axes=False, xlabel="涨跌幅区间", title=title)
        return bar_pct_chg

    def _deal_with_today(self):
        df_y = self.df_yesterday.copy()
        df_t = self.df_today.copy()
        df1 = df_y.drop(columns=['date', 'pct_chg'])
        df_t = pd.merge(df_t, df1, on='code')
        df_t.dropna(inplace=True)
        return df_t

    def html_daily(self):
        df_y = self.df_yesterday.copy()
        df_t = self._deal_with_today()
        bar_cap = self.__html_cap(df_y)
        bar_pct_chg = self.__html_pct_chg(df_y)
        layout = self.__html_cap(df_t) + self.__html_pct_chg(df_t) + bar_cap + bar_pct_chg
        layout.opts().cols(2)
        print(layout)
        hv.save(layout, self.inc_dir + "inc_daily.html")

    def __html_range(self, date_s=None, date_e=None, des=None):
        df_range = self.ld.get_pre_cap_chg(date_s=date_s, date_e=date_e)
        df_t = self._deal_with_today()
        df_range = pd.concat([df_range, df_t])

        ddf = df_range.groupby('code').apply(cal_range_pct_chg_and_cap)
        layout = self.__html_cap(ddf, daily=False, des=des) + self.__html_pct_chg(ddf, daily=False, des=des)
        layout.opts().cols(2)
        print(layout)
        return layout

    def html_weekly(self):
        week_s, week_e = get_week_month_date(week=True)
        layout = self.__html_range(week_s, week_e, des='本周')
        hv.save(layout, self.inc_dir + "inc_weekly.html")

    def html_monthly(self):
        month_s, month_e = get_week_month_date(month=True)
        layout = self.__html_range(month_s, month_e, des='本月')
        hv.save(layout, self.inc_dir + "inc_monthly.html")


def cal_range_pct_chg_and_cap(df_from):
    df = df_from.copy()
    cap_mean = df.mkt_cap_ard.mean()
    pct_chg = (df.pct_chg + 1).cumprod().iloc[-1] - 1
    res = pd.Series({'date_s': df.date.values[0], 'date_e': df.date.values[-1],
                     'mkt_cap_ard': cap_mean, 'pct_chg': pct_chg})
    return res


if __name__ == '__main__':
    xx = StatisticView()
    xx.html_daily()
    xx.html_weekly()
    xx.html_monthly()
    xx.ld.close()
