#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/3 9:35
# @Author  : Neo
# @File    : views_plotly.py
# @Software: PyCharm
# 说明:
import datetime

from plotly import graph_objs as go
import plotly.express as px
import pandas as pd
from Datas.db_client import get_client
from ShuiDQReport.settings import BASE_DIR

pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('expand_frame_repr', False)
pd.set_option('display.max_columns', None)
pd.set_option('display.precision', 14)


class PlotLoss:
    def __init__(self, pro='DQ_ZX'):
        self.pro = pro
        _client = get_client(c_from='neo')

        self.df_loss = None
        if self.pro == 'DQ_ZX':
            self.pro_name = '碓泉@1号（中信端）'
            self.t_ = _client['statistic']['loss_alpha_first']
            self.inc_dir = str(BASE_DIR) + "/TradeLoss/templates/TradeLoss/dq_zx/"
        elif self.pro == 'ALPHA_ALL':
            self.pro_name = '产品(@1号)'
            self.t_ = _client['statistic']['loss_alpha_all']
            self.inc_dir = str(BASE_DIR) + "/TradeLoss/templates/TradeLoss/dq_hx/"
        elif self.pro == 'MARGIN':
            self.pro_name = '碓泉@1号（股衍）'
            self.t_ = _client['statistic']['loss_alpha_first_margin']
            self.inc_dir = str(BASE_DIR) + "/TradeLoss/templates/TradeLoss/dq_hx/"
        elif self.pro == 'DQ_HX':
            self.pro_name = '碓泉@1号（华西端）'
            self.t_ = _client['statistic']['loss_alpha_first_hx']
            self.inc_dir = str(BASE_DIR) + "/TradeLoss/templates/TradeLoss/dq_hx/"
        elif self.pro == 'DQ_DF':
            self.pro_name = '碓泉@1号（东方端）'
            self.t_ = _client['statistic']['loss_alpha_first_df']
            self.inc_dir = str(BASE_DIR) + "/TradeLoss/templates/TradeLoss/dq_df/"
        elif self.pro == 'YK_CJ':
            self.pro_name = '屿阔1号 - 长江'
            self.t_ = _client['statistic']['loss_yk_first']
            self.inc_dir = str(BASE_DIR) + "/TradeLoss/templates/TradeLoss/yk_cj/"
        else:
            raise Exception('到底哪个产品？？')

        self.height = 888

    def _load_df_loss(self):
        if self.df_loss is None:
            df_loss = pd.DataFrame(self.t_.find({}, {"_id": 0, }))
            self.df_loss = df_loss

    def plot_the_date(self, the_date=None):
        width, height = 800, 600
        if self.df_loss is None:
            self._load_df_loss()
        df = self.df_loss.copy()
        if the_date is None:
            the_date = df.iloc[-1].date

        dx = df.loc[df.date == the_date].iloc[0]

        df1 = pd.DataFrame(data=[('交易总额', 'REB', 'reb', dx.trade_sum_reb),
                                 ('交易总额', '换仓', '换入', dx.trade_sum_sell),
                                 ('交易总额', '换仓', '换出', dx.trade_sum_buy)], columns=['sum', '类型', '方向', 'value'])
        df1 = df1.loc[df1.value > 0]

        fig_trade_value = px.sunburst(df1, path=['sum', '类型', '方向'], values='value', color='value',
                                      title=f"各种类型交易金额: {the_date}",
                                      width=height, height=height)
        fig_trade_value.update_traces(textinfo='label+value+percent root')
        fig_trade_value.update_coloraxes(showscale=False)

        x_list = ['整体', '换手', 'REB']

        at_list = [dx.mis_sum, dx.mis_sum_turn, dx.mis_sum_reb]
        twap_list = [dx.mis_sum_mean, dx.mis_sum_turn_mean, dx.mis_sum_reb_mean]
        fig_loss_value = go.Figure(data=[
            go.Bar(x=x_list, y=at_list, name='截面', text=[format(x, '.0f') for x in at_list], textposition='outside'),
            go.Bar(x=x_list, y=twap_list, name='TWAP', text=[format(x, '.0f') for x in twap_list], textposition='outside'),
        ],
            layout={
                'height': height,
                'title': "各种订单损失金额",
                "font": {"size": 22, },
            })

        at_list = [x * 100 for x in [dx.mis_cent, dx.mis_cent_turn, dx.mis_cent_reb]]
        twap_list = [x * 100 for x in [dx.mis_cent_mean, dx.mis_cent_turn_mean, dx.mis_cent_reb_mean]]
        fig_loss = go.Figure(data=[
            go.Bar(x=x_list, y=at_list, name='截面', text=[format(x / 100, '.2%') for x in at_list], textposition='outside'),
            go.Bar(x=x_list, y=twap_list, name='TWAP', text=[format(x / 100, '.2%') for x in twap_list], textposition='outside'),
        ],
            layout={
                'height': height,
                'title': f"{the_date} ~ 各种订单损失百分比",
                "font": {"size": 22, },
                "yaxis": {"title": '损失百分比', "ticksuffix": "%", "showgrid": True},
            })

        return fig_loss, fig_loss_value, fig_trade_value

    def plot_all_area(self, ma=20, twap=False):
        if self.df_loss is None:
            self._load_df_loss()
        df = self.df_loss.copy()
        if twap:
            dx = df[['date', 'mis_cent_mean', 'mis_cent_reb_mean', 'mis_cent_turn_mean']].copy()
            dx.rename(columns={'mis_cent_mean': 'mis_cent', 'mis_cent_reb_mean': 'mis_cent_reb',
                               'mis_cent_turn_mean': 'mis_cent_turn'}, inplace=True)
            ss = '交易时段TWAP（分钟成交量加权）'
        else:
            dx = df[['date', 'mis_cent', 'mis_cent_reb', 'mis_cent_turn', ]].copy()
            ss = '参照第一笔订单发生时刻'
        
        today= list(self.t_ .find({}, {'_id': 0, 'date': 1}).sort([('date', -1)]).limit(1))[0].get('date')



        dx["all_day"]=dx.mis_cent.rolling(ma).mean()
        dx["reb_day"]=dx.mis_cent_reb.rolling(ma).mean()
        dx["turn_day"]=dx.mis_cent_turn.rolling(ma).mean()

        all_day= dx[dx['date'] == '{}'.format(today)]
        all_day_value = all_day['all_day'].values[0] 
        reb_day_value = all_day['reb_day'].values[0] 
        turn_day_value= all_day['turn_day'].values[0]




        # mode还可以设置为none，表示将线段隐藏
        area0 = go.Scatter(x=dx.date, y=dx.mis_cent * 100, name="所有订单", mode="none", fill="tonexty")
        line0 = go.Scatter(x=dx.date, y=dx.mis_cent.rolling(ma).mean() * 100, name=f"所有订单(MA={ma})")
        area1 = go.Scatter(x=dx.date, y=dx.mis_cent_reb * 100, name="Reb", mode="none", fill="tonexty")
        line1 = go.Scatter(x=dx.date, y=dx.mis_cent_reb.rolling(ma).mean() * 100, name=f"Reb(MA={ma})")
        area2 = go.Scatter(x=dx.date, y=dx.mis_cent_turn * 100, name="Turn", mode="none", fill="tonexty")
        line2 = go.Scatter(x=dx.date, y=dx.mis_cent_turn.rolling(ma).mean() * 100, name=f"Turn(MA={ma})")

        mean_all = format(dx.mis_cent.mean(), '.4%')
        mean_reb = format(dx.mis_cent_reb.mean(), '.4%')
        mean_turn = format(dx.mis_cent_turn.mean(), '.4%')
        all_day = format(all_day_value, '.4%')
        reb_day = format(reb_day_value, '.4%')
        turn_day = format(turn_day_value, '.4%')

        fig = go.Figure(data=[area0, area1, area2, line0, line1, line2],
                        layout={
                            'height': 700,
                            "title": f"""{self.pro_name} ~ {ss} - MEAN(all):{mean_all},MEAN(reb):{mean_reb},MEAN(turn):{mean_turn},<br>
                            {today} ~ MA20(all):{all_day},MA20(reb):{reb_day},MA20(turn):{turn_day}""",
                            "font": {"size": 22, },
                            # 'legend': {'orientation': "v", 'yanchor': 'auto', 'xanchor': 'center', },
                            "xaxis": {
                                "zerolinecolor": "red",
                                "zerolinewidth": 5},
                            "yaxis": {"ticksuffix": "%", "showgrid": True},
                        })
        return fig
        # fig.write_html(self.inc_dir + "inc_area_and_lines.html")

    def plot_latest_days(self, days=10, twap=False):
        if self.df_loss is None:
            self._load_df_loss()
        df = self.df_loss.copy()
        if twap:
            dx = df.sort_values('date').iloc[0 - days:][['date', 'mis_cent_mean', 'mis_cent_reb_mean', 'mis_cent_turn_mean']].copy()
            dx.rename(columns={'mis_cent_mean': 'mis_cent', 'mis_cent_reb_mean': 'mis_cent_reb',
                               'mis_cent_turn_mean': 'mis_cent_turn'}, inplace=True)
            ss = '交易时段TWAP（分钟成交量加权）'
        else:
            dx = df.sort_values('date').iloc[0 - days:][['date', 'mis_cent', 'mis_cent_reb', 'mis_cent_turn', ]]
            ss = '参照第一笔订单发生时刻'

        bar0 = go.Bar(x=dx.date, y=dx.mis_cent * 100, name="All")
        bar1 = go.Bar(x=dx.date, y=dx.mis_cent_reb * 100, name="Reb")
        bar2 = go.Bar(x=dx.date, y=dx.mis_cent_turn * 100, name="Turn")

        mean_all = format(dx.mis_cent.mean(), '.4%')
        mean_reb = format(dx.mis_cent_reb.mean(), '.4%')
        mean_turn = format(dx.mis_cent_turn.mean(), '.4%')
        fig = go.Figure(data=[bar0, bar1, bar2],
                        layout={
                            'height': 700,
                            # "barmode": "stack",
                            "title": f"{self.pro_name}近 {days} 日  ~ {ss} ~ MEAN(all)：{mean_all}，MEAN(reb)：{mean_reb}，MEAN(turn)：{mean_turn}",
                            "font": {"size": 22, },
                            'legend': {'orientation': "v", 'yanchor': 'auto', 'xanchor': 'center', },
                            'xaxis': {'tickformat': "%m-%d", 'nticks': 15, "tickangle": 90, "showgrid": True},
                            "yaxis": {"ticksuffix": "%", "showgrid": True}, }
                        )
        return fig
        # fig.write_html(self.inc_dir + "inc_laest_sum_and_cent_bar.html")

    def plot_latest_freq(self, freq='weekly', count=10, twap=False):
        if self.df_loss is None:
            self._load_df_loss()
        df = self.df_loss.copy()
        if twap:
            dx = df[['date', 'mis_cent_mean', 'mis_cent_reb_mean', 'mis_cent_turn_mean']].copy()
            dx.rename(columns={'mis_cent_mean': 'mis_cent', 'mis_cent_reb_mean': 'mis_cent_reb',
                               'mis_cent_turn_mean': 'mis_cent_turn'}, inplace=True)
            ss = '交易时段TWAP（分钟成交量加权）'
        else:
            dx = df[['date', 'mis_cent', 'mis_cent_reb', 'mis_cent_turn', ]].copy()
            ss = '参照第一笔订单发生时刻'
        dx['date'] = pd.to_datetime(dx.date)
        if freq == "weekly":
            dx['freq_day'] = dx.date.map(lambda x: str(x - datetime.timedelta(days=x.weekday()))[:10])
        elif freq == 'monthly':
            dx['freq_day'] = dx.date.map(lambda x: str(datetime.datetime(x.year, x.month, 1))[:7])
        else:
            raise Exception(f'周、月？？')
        freqs = dx.freq_day.unique().tolist()
        dx = dx[dx.freq_day.isin(freqs[-count:])]

        box0 = go.Box(x=dx.freq_day, y=dx.mis_cent * 100, name="All", boxpoints='all', )
        box1 = go.Box(x=dx.freq_day, y=dx.mis_cent_reb * 100, name="Reb", boxpoints='all')
        box2 = go.Box(x=dx.freq_day, y=dx.mis_cent_turn * 100, name="Turn", boxpoints='all')
        mean_all = format(dx.mis_cent.mean(), '.4%')
        mean_reb = format(dx.mis_cent_reb.mean(), '.4%')
        mean_turn = format(dx.mis_cent_turn.mean(), '.4%')
        fig = go.Figure(data=[box0, box1, box2],
                        layout={
                            'height': 700,
                            'boxmode': 'group',
                            "title": f"{self.pro_name} 近 {count} {freq} ~ {ss} MEAN(all)：{mean_all}，MEAN(reb)：{mean_reb}，MEAN(turn)：{mean_turn}",
                            "font": {"size": 22, },
                            'legend': {'orientation': "v", 'yanchor': 'auto', 'xanchor': 'center', },
                            # 'xaxis': {'dtick': "M2", 'tickformat': "%Y-%m", 'nticks': 15, "tickangle": 90, "showgrid": True},
                            "yaxis": {"ticksuffix": "%", "showgrid": True, },
                        })
        return fig
        # fig.write_html(res_file)


def loss_plotly():
    for pro in ['DQ_ZX', 'DQ_HX', 'DQ_DF', 'YK_CJ']:
        xx = PlotLoss(pro=pro)
        xx.plot_all_area(ma=20)
        xx.plot_latest_days()
        xx.plot_the_date()
        xx.plot_latest_freq(freq='weekly', count=10)
        xx.plot_latest_freq(freq='monthly', count=10)


if __name__ == '__main__':
    # xx = PlotLoss(pro='DQ_ZX')
    loss_plotly()
