#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/5 16:47
# @Author  : Neo
# @File    : views.py
# @Software: PyCharm
# 说明:
from django.shortcuts import render

import pandas as pd
from Datas.db_client import get_client
from plotly import graph_objs as go
import plotly.express as px

pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('expand_frame_repr', False)
pd.set_option('display.max_columns', None)
pd.set_option('display.precision', 14)


def _plot_net_back(ddf: pd.DataFrame, pro: str):
    """净值 & 回撤"""
    df = ddf.copy()
    for i in range(df.shape[0]):
        df.loc[i, 'max_value'] = df.loc[:i].累计净值.max()
    df['back'] = df['累计净值'] / df['max_value'] - 1

    g1 = go.Scatter(x=df['date'], y=df['累计净值'], name='累计净值')
    g2 = go.Scatter(x=df['date'], y=df['back'] * 100, name='净值回撤', xaxis='x', yaxis='y2', mode="none", fill="tozeroy")
    chg_all = format(df['累计净值'].iloc[-1] / df['累计净值'].iloc[0] - 1, '.2%')
    chg_ana = format(df['累计净值'].iloc[-1] ** (252 / df.shape[0]) - 1, '.2%')
    date_s = df.iloc[0].date
    date_e = df.iloc[-1].date
    fig = go.Figure(data=[g1, g2, ],
                    layout={
                        'height': 999,
                        "title": f"{pro}({date_s} ~ {date_e})，累计收益：{chg_all}，年化收益：{chg_ana}",
                        "font": {"size": 22, },
                        "yaxis": {"title": "累计净值", },
                        "yaxis2": {"title": "最大回撤", "side": "right", "overlaying": "y", "ticksuffix": "%", "showgrid": False, },
                    })
    return fig.to_html(full_html=False, include_plotlyjs=True)


def _plot_net_value(ddf: pd.DataFrame, pro: str):
    df = ddf.copy()
    line0 = go.Scatter(x=df['date'], y=df['累计净值'], name=f"累计净值")
    area0 = go.Scatter(x=df['date'], y=df['资产净值'] * 1, name="资产净值", mode="none", fill="tonexty", yaxis="y2",
                       xaxis="x2")
    area1 = go.Scatter(x=df['date'], y=df['实收资本'] * 1, name="实收资本", mode="none", fill="tonexty", yaxis="y2",
                       xaxis="x2")

    chg_all = format(df['累计净值'].iloc[-1] / df['累计净值'].iloc[0] - 1, '.2%')
    chg_ana = format(df['累计净值'].iloc[-1] ** (252 / df.shape[0]) - 1, '.2%')
    fig0 = go.Figure(data=[line0, area1, area0, ],
                     layout={
                         'height': 999,
                         "title": f"{pro} - 净值 & 资产走势，累计收益：{chg_all}，年化收益：{chg_ana}",
                         "font": {"size": 22, },
                         "xaxis": {"showgrid": False, "zeroline": False},
                         "yaxis": {"title": "累计净值", "showgrid": True},
                         "xaxis2": {"overlaying": "x"},  # 必须要写，否则图像无法显示# 同理下面的yaxis也是类似
                         "yaxis2": {"title": "MONEY", "side": "right", "overlaying": "y"},
                     })
    return fig0.to_html(full_html=False, include_plotlyjs=True)


def _plot_hot_map(ddf: pd.DataFrame, pro: str):
    df = ddf.copy()
    date1 = df.iloc[0].date
    date2 = df.iloc[-1].date
    df['month'] = df['date'].map(lambda x: x[:7])
    df['year'] = df['date'].map(lambda x: x[:4])
    sx = df.groupby(['year', 'month']).apply(lambda d: ((d.pct_chg + 1).cumprod() - 1).iloc[-1])
    sx.name = 'pct_chg'
    dx = sx.reset_index(level=[0, 1])

    win_po = format(dx.loc[dx.pct_chg >= 0].shape[0] / dx.shape[0], '.2%')
    win_lo = format(dx.loc[dx.pct_chg >= 0].pct_chg.mean() / abs(dx.loc[dx.pct_chg < 0].pct_chg.mean()), '.2f')
    dx['month'] = dx.month.map(lambda x: x[-2:])

    if len(df.year.unique().tolist()) > 1:
        sy = df.groupby('year').apply(lambda d: ((d.pct_chg + 1).cumprod() - 1).iloc[-1])
        sy.name = 'pct_chg'
        dy = sy.reset_index(level=0)
        dy.insert(1, 'month', '全年')
        dxx = pd.concat((dx, dy))
        dx1 = dxx.groupby('month')['pct_chg'].mean().reset_index().iloc[:-1]
    else:
        year = df.year.unique().tolist()[0]
        chg = ((df.pct_chg + 1).cumprod() - 1).iloc[-1]
        dy = pd.DataFrame([(year, '全年', chg), ], columns=['year', 'month', 'pct_chg'])
        dxx = pd.concat((dx, dy))
        ss = dxx.groupby('month').apply(lambda d: d.iloc[-1].pct_chg)
        ss.name = 'pct_chg'
        dx1 = ss.reset_index().iloc[:-1]

    dx1.insert(0, 'year', 'MEAN')
    dxxx = pd.concat((dxx, dx1))

    trace0 = go.Heatmap(x=dxxx.month,
                        y=dxxx.year,
                        z=dxxx.pct_chg,
                        text=dxxx.pct_chg.map(lambda x: format(x, '.2%')),
                        texttemplate="%{text}",
                        zmin=dx.pct_chg.min(), zmax=dx.pct_chg.max())
    fig1 = go.Figure(
        data=[trace0],
        layout={
            # 'height': 888,
            "title": f"{pro}（{date1} ~ {date2}） - 月胜率：{win_po} ~ 月盈亏比：{win_lo}",
            "font": {"size": 22, },
            "xaxis": {"side": "top", },
        }
    )
    # fig1.show()
    return fig1.to_html(full_html=False, include_plotlyjs=True)


def firm_index(request, pro_id: str):
    db = get_client(c_from='neo')['product']
    if pro_id == 'SEY112':
        pro = '可变阿尔法一号'
        t = db['net_value_alpha_first']
    elif pro_id == 'SB5663':
        pro = '屿阔一号'
        t = db['net_value_yk_first']
    else:
        raise Exception(f'指定产品名有误！！！')

    df = pd.DataFrame(t.find({}, {'_id': 0, '单位净值': 0})).sort_values('date')
    df['pct_chg'] = df['累计净值'].pct_change().fillna(0)

    net_back = _plot_net_back(df, pro)
    if request.user.is_superuser:
        net_sst = _plot_net_value(df, pro)
    else:
        net_sst = None
    chg_detail = _plot_hot_map(df[['date', 'pct_chg']], pro)

    return render(request, "firm_offer/index.html", {'pro': pro,
                                                     'net_back': net_back,
                                                     "net_sst": net_sst,
                                                     'chg_detail': chg_detail})


def pdf_detail(request):
    return render(request, "firm_offer/luyan.html", {})
