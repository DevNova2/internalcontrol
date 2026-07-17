# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: views.py
@time: 2023/5/15 20:11
说明:
"""
from django.shortcuts import render
from TradeLoss.views_plotly import PlotLoss
import pandas as pd
from Datas.db_client import get_client
import plotly.express as px
import plotly.graph_objs as go


def _load_loss_plot(t_, the_date=None, pro=None):
    width, height = 800, 600
    if the_date is None:
        the_date = next(t_.find({}, {'_id': 0, 'date': 1}).sort([('date', -1), ]).limit(1)).get('date')
    df = pd.DataFrame(t_.find({'date': the_date}, {"_id": 0, }))
    dx = df.loc[df.date == the_date].iloc[0]

    df1 = pd.DataFrame(data=[('交易总额', 'REB', 'reb', dx.trade_sum_reb),
                             ('交易总额', '换仓', '换入', dx.trade_sum_buy),
                             ('交易总额', '换仓', '换出', dx.trade_sum_sell)], columns=['sum', '类型', '方向', 'value'])
    df1 = df1.loc[df1.value > 0]
    fig_trade_value = px.sunburst(df1, path=['sum', '类型', '方向'], values='value', color='value',
                                  title=f"各种类型交易金额:{the_date},{pro}", width=height, height=height)
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


def loss_the_date(request, the_date=None):
    db = get_client(c_from='neo')
    t_list = {
        '产品：阿尔法1号': 'loss_alpha_all',
        '阿尔法1号（股衍）': 'loss_alpha_first_margin',
        '阿尔法1号（东方）': 'loss_alpha_first_df',
        # '屿阔1号（长江）': 'loss_yk_first'
    }
    res_list = []
    for k, t in t_list.items():
        t_ = db['statistic'][t]
        fig_loss, fig_loss_value, fig_trade_value = _load_loss_plot(t_, the_date=the_date, pro=k)
        res_list.append((
            fig_loss.to_html(full_html=False, include_plotlyjs=True),
            fig_loss_value.to_html(full_html=False, include_plotlyjs=True),
            fig_trade_value.to_html(full_html=False, include_plotlyjs=True),
        ))
    return render(request, "TradeLoss/pro_list.html", {"pro_list": res_list, })


def loss_index(request, pro=None):
    xx = PlotLoss(pro=pro)
    pro = xx.pro_name
    fig_all = xx.plot_all_area(ma=20, twap=False)
    fig_all_twap = xx.plot_all_area(ma=20, twap=True)

    fig_loss, fig_loss_value, fig_trade_value = xx.plot_the_date()

    fig_latest = xx.plot_latest_days(days=10, twap=False)
    fig_latest_twap = xx.plot_latest_days(days=10, twap=True)

    fig_weekly = xx.plot_latest_freq(freq='weekly', count=10, twap=False)
    fig_weekly_twap = xx.plot_latest_freq(freq='weekly', count=10, twap=True)

    fig_monthly = xx.plot_latest_freq(freq='monthly', count=10, twap=False)
    fig_monthly_twap = xx.plot_latest_freq(freq='monthly', count=10, twap=True)

    return render(request, "TradeLoss/index.html",
                  {
                      "fig_all": fig_all.to_html(full_html=False, include_plotlyjs=True),
                      "fig_all_twap": fig_all_twap.to_html(full_html=False, include_plotlyjs=True),

                      'html_loss': fig_loss.to_html(full_html=False, include_plotlyjs=True),
                      'html_loss_value': fig_loss_value.to_html(full_html=False, include_plotlyjs=True),
                      'html_trade_value': fig_trade_value.to_html(full_html=False, include_plotlyjs=True),

                      'fig_latest': fig_latest.to_html(full_html=False, include_plotlyjs=True),
                      'fig_latest_twap': fig_latest_twap.to_html(full_html=False, include_plotlyjs=True),
                      'html_weekly': fig_weekly.to_html(full_html=False, include_plotlyjs=True),
                      'html_weekly_twap': fig_weekly_twap.to_html(full_html=False, include_plotlyjs=True),
                      'html_monthly': fig_monthly.to_html(full_html=False, include_plotlyjs=True),
                      'html_monthly_twap': fig_monthly_twap.to_html(full_html=False, include_plotlyjs=True),
                      'pro': pro})
