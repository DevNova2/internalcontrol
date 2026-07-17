# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: vis_alpha_one.py
@time: 2023/5/26 13:57
说明:
"""
import numpy as np
import pandas as pd
import hvplot
import hvplot.pandas  # noqa

import holoviews as hv
from holoviews import opts
from holoviews import dim

from ShuiDQReport.settings import BASE_DIR
from mult_factor.load_data import LoadData
from Datas import stat
import warnings

warnings.filterwarnings('ignore', category=FutureWarning)
pd.options.plotting.backend = 'holoviews'
hv.extension('bokeh')


def cal_VaR_and_ES(series):
    VaR_60 = series.quantile(0.4)
    ES_60 = series[series <= VaR_60].mean()
    VaR_90 = series.quantile(0.1)
    ES_90 = series[series <= VaR_90].mean()
    VaR_95 = series.quantile(0.05)
    ES_95 = series[series <= VaR_95].mean()
    VaR_99 = series.quantile(0.01)
    ES_99 = series[series <= VaR_99].mean()
    VaR_9999 = series.quantile(0.001)
    ES_9999 = series[series <= VaR_9999].mean()
    h_VaR = {'60%': [VaR_60, ES_60], '90%': [VaR_90, ES_90], '95%': [VaR_95, ES_95], '99%': [VaR_99, ES_99],
             '99.99%': [VaR_9999, ES_9999]}
    # columns = [('1D', 'VaR'), ('1D', 'ES')]
    # pd.DataFrame.from_dict(h_VaR, orient='index', columns=pd.MultiIndex.from_tuples(columns))
    return pd.DataFrame.from_dict(h_VaR, orient='index', columns=['VaR', 'ES'])


class StrategyView(object):
    def __init__(self, ld, stra_name="alpha_one"):
        self.stra_name = stra_name
        self.inc_dir = str(BASE_DIR) + "/mult_factor/templates/mult_factor/" + self.stra_name + "/"

        self.df = ld.get_pt_chg(stra_name=stra_name)
        self.ld = ld

    def html_all(self):
        df_plot = self.df.copy()
        df_plot["date"] = pd.to_datetime(df_plot.index)
        df_plot = stat.stat_max(df_plot, col='net_value4_')
        df_plot['back'] = df_plot['net_value4_'] / df_plot['max_value'] - 1
        df_plot['back_per'] = (df_plot.back * 100).round(2)

        the_date = df_plot.loc[df_plot.back.idxmin(), 'date']
        the_pos = df_plot.loc[df_plot.back.idxmin(), 'net_value4_']
        point_max_back = hv.Points(pd.DataFrame(dict(x=[the_date, ], y=[the_pos, ], ))).opts(size=6)
        text = '历史最大回撤点\n日期：{}，幅度：{:.2%}'.format(str(the_date)[:10], df_plot.back.min())
        text_max_back = hv.Text(the_date, the_pos, text=text, valign='top', halign='left')

        alpha_chg = df_plot.iloc[-1]['net_value4_'] - 1
        # 策略年化收益率
        alpha_annual = (df_plot.iloc[-1]['net_value4_']) ** (252 / df_plot.shape[0]) - 1
        alpha_std = 21 ** 0.5 * df_plot.chg.std()
        alpha_sharp = 252 ** 0.5 * df_plot.chg.mean() / df_plot.chg.std()
        title = '【{} - {}】总收益：{:.2%}，年化收益：{:.2%}，月波动率：{:.2%}，年化夏普率：{:.2f}'.format(
            str(df_plot.iloc[0]['date'])[:10], str(df_plot.iloc[-1]['date'])[:10],
            alpha_chg, alpha_annual, alpha_std, alpha_sharp)
        curve = hv.Curve(df_plot, 'date', 'net_value4_')
        lay1 = curve * point_max_back * text_max_back
        lay1.opts(
            opts.Curve(height=self.ld.high, width=self.ld.width2, line_width=1.50, color='red', tools=['hover'], title=title, show_grid=True, ),
        )

        back_dim = hv.Dimension('back_per', label='回撤比列', unit='%')
        spikes = hv.Spikes(df_plot, 'date', back_dim).opts(xaxis=None, color='grey', tools=['hover'])
        turn_title = "换手率(标红) & 回撤(标灰) & 持仓量(蓝线) 指标 --->>> 平均单边换手率 {:.2%}）".format(df_plot.turnover.mean())
        df_plot['turnover_per'] = (df_plot.turnover * 100).round(2)
        turnover_dim = hv.Dimension('turnover_per', label='换手率', unit='%')
        turn_spikes = hv.Spikes(df_plot, 'date', turnover_dim).opts(
            xaxis=None, color='purple', title=turn_title, ylabel="换手率 & 回撤 & 持仓量")
        curve_hold = hv.Curve(df_plot, 'date', 'hold_num')
        lay2 = spikes * turn_spikes * curve_hold
        lay2.opts(
            opts.Curve(height=self.ld.high, width=self.ld.width2, xaxis=None, line_width=1.50, color='blue',
                       tools=['hover'], title=title),
            opts.Spikes(height=200, width=self.ld.width2, line_width=0.25)
        )

        df_plot['chg_per'] = (df_plot.chg * 100).round(2)
        chg_dim = hv.Dimension('chg_per', label='涨跌幅', unit='%')
        chg_scatter = hv.Scatter(df_plot, 'date', chg_dim).opts(size=abs(dim('chg_per')), color=np.sign(dim('chg_per')))

        lay3 = chg_scatter * chg_scatter.hist()
        lay3.opts(
            opts.Scatter(height=200, tools=['hover'], width=self.ld.width2, title="每日涨跌幅 & 分布"),
            opts.Histogram(tools=['hover']),
        )

        layout = lay1 + lay2 + lay3
        layout.opts().cols(1)

        print(layout)
        hv.save(layout, self.inc_dir + "inc_all.html")

    def html_VaR_ES(self):
        df = self.df.copy()
        df.sort_values('date', inplace=True)
        days = [5, 10, 20, 40, 60, 120, 240, 480, 720, 960, 1200]
        df_VaR, df_ES = pd.DataFrame(), pd.DataFrame()
        for day in days:
            returns = df['net_value4_'].pct_change(day)
            returns.dropna(inplace=True)
            df_tmp = cal_VaR_and_ES(returns)
            df_VaR = pd.concat([df_VaR, df_tmp[['VaR']].rename(columns={'VaR': str(day) + '个交易日'})], axis=1)
            df_ES = pd.concat([df_ES, df_tmp[['ES']].rename(columns={'ES': str(day) + '个交易日'})], axis=1)
            # df_VaR.columns = pd.MultiIndex.from_tuples([('持有交易日：' + str(day), 'VaR'), ('持有交易日：' + str(day), 'ES')])
            # df_VRES = pd.concat([df_VRES, df_VaR], axis=1)
        # df_VaR = df_VaR.applymap(lambda x: '{:.2%}'.format(x))
        df_VaR = df_VaR.round(4) * 100
        # df_VaR.insert(0, '置信区间', df_VaR.index)
        # df_VaR.reset_index(inplace=True, drop=True)
        # df_ES = df_ES.applymap(lambda x: '{:.2%}'.format(x))
        df_ES = df_ES.round(4) * 100
        # df_ES.insert(0, '置信区间', df_ES.index)
        # df_ES.reset_index(inplace=True, drop=True)

        table1 = df_VaR.hvplot.heatmap(
            x='columns', y='index',
            title="组合 {}，任意持有期对应置信区间的 VaR(上) & ES(下)，算法：历史模拟法【{} - {}】，单位：%".format(
                self.stra_name, str(df.iloc[0]['date'])[:10], str(df.iloc[-1]['date'])[:10], ),
            cmap=["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce", "#ddb7b1", "#cc7878", "#933b41"],
            symmetric=True,  # 0 为中间值
            width=self.ld.width2, height=300).opts(fontsize={'title': 15, 'xticks': 12, 'yticks': 12})
        table2 = df_ES.hvplot.heatmap(
            x='columns', y='index',
            cmap=["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce", "#ddb7b1", "#cc7878", "#933b41"],
            symmetric=True,  # 0 为中间值
            xaxis=False, width=self.ld.width2, height=300).opts(fontsize={'title': 15, 'xticks': 12, 'yticks': 12})

        # table1 = df_VaR.hvplot.table(sortable=True, selectable=True,
        #                              title="组合 {}，任意持有期对应置信区间的VaR，（算法：历史模拟法）".format(
        #                                  self.stra_name))
        # table2 = df_ES.hvplot.table(sortable=True, selectable=True,
        #                             title="组合 {}，任意持有期对应置信区间的ES，（算法：历史模拟法）".format(
        #                                 self.stra_name))

        layout = table1 * hv.Labels(table1).opts(padding=0) + table2 * hv.Labels(table2).opts(padding=0)
        layout.opts().cols(1)

        print(layout)
        hv.save(layout, self.inc_dir + "inc_VaR_ES.html")


if __name__ == '__main__':
    ld = LoadData()
    stra_list = ["alpha_first", 'yk_first']
    for stra in stra_list:
        alpha = StrategyView(ld=ld, stra_name=stra)
        alpha.html_all()
        # alpha.html_VaR_ES()
    ld.close()
