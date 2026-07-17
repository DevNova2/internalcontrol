from django.shortcuts import render, redirect
import pandas as pd
from Utils.utils import get_week_month_date
from Datas.db_client import get_client
from plotly import graph_objs as go


def _plot(df_left, df_right, title, m):
    if m == 'D':
        domain1, domain2 = [0, 0.45], [0.5, 1]
        df_right = df_right.loc[(df_right.bins > -22) & (df_right.bins < 22)]
    elif m == 'W':
        domain1, domain2 = [0, 0.3], [0.35, 1]
        df_right = df_right.loc[(df_right.bins > -41) & (df_right.bins < 41)]
    elif m == 'M':
        domain1, domain2 = [0, 0.2], [0.25, 1]
        df_right = df_right.loc[(df_right.bins > -51) & (df_right.bins < 51)]
    else:
        domain1, domain2 = [0, 0.1], [0.15, 1]
        df_right = df_right.loc[(df_right.bins > -65) & (df_right.bins < 65)]
    #
    df_left['sort_no'] = df_left.index.map(lambda x: '0' if x == 'Large' else x)
    df_left['color'] = df_left.chg_mean.map(lambda x: 'red' if x > 0 else 'green')
    df_left.sort_values('sort_no', inplace=True)

    trace0 = go.Bar(x=df_left.index, y=df_left.chg_mean * 100, marker={'color': df_left.color})
    trace1 = go.Bar(x=df_right.bins, y=df_right.value, xaxis="x2", yaxis="y2", marker={'color': df_right.color})

    all_counts = df_right.value.sum()
    red_counts = format(df_right[df_right.bins > 0].value.sum() / all_counts, '.2%')
    blue_counts = format(df_right[df_right.bins < 0].value.sum() / all_counts, '.2%')
    zero_counts = format(df_right[df_right.bins == 0].value.sum() / all_counts, '.2%')

    fig = go.Figure(data=[trace0, trace1, ],
                    layout={
                        'height': 888,
                        "title": f'{title}，红军：{red_counts}，绿军：{blue_counts}，十字军：{zero_counts}',
                        "font": {"size": 17, },
                        'showlegend': False,
                        "xaxis": {"domain": domain1, 'title': '按市值分组'},
                        "yaxis": {"title": "涨跌幅", "ticksuffix": "%", },
                        "xaxis2": {"domain": domain2, 'dtick': 1, 'title': '涨跌幅'},
                        "yaxis2": {"anchor": "x2", "title": "分布数量", },
                    })
    # fig.show()
    return fig.to_html(full_html=False, include_plotlyjs=True)


def chg_dist(request, the_date='latest'):
    db_ = get_client(c_from='neo')['statistic']
    if the_date == 'latest':
        the_date = next(db_['quo_chg'].find({}, {'_id': 0, 'date': 1}).sort([('date', -1), ]).limit(1)).get('date')
    else:
        the_date = next(db_['quo_chg'].find({'date': {'$lte': the_date}}, {'_id': 0, 'date': 1}).sort([('date', -1), ]).limit(1)).get(
            'date')
    d_w_s, d_w_e = get_week_month_date(the_date=the_date, week=True, month=False)
    d_m_s, d_m_e = get_week_month_date(the_date=the_date, week=False, month=True)
    year_s = str(the_date)[:4] + '-01-01'

    df = pd.DataFrame(
        db_['quo_chg'].find({'date': {'$gte': min(d_w_s, d_m_s, year_s), '$lte': the_date}}, {'_id': 0, },
                            batch_size=1000000)).set_index(
        'date').sort_index()
    df_today = df.loc[the_date].set_index('gro')

    s_week = df.loc[d_w_s:].groupby('gro').apply(lambda ddf: (ddf.chg_mean + 1).cumprod().iloc[-1] - 1)
    df_week = s_week.rename('chg_mean').reset_index().set_index('gro')
    s_month = df.loc[d_m_s:].groupby('gro').apply(lambda ddf: (ddf.chg_mean + 1).cumprod().iloc[-1] - 1)
    df_month = s_month.rename('chg_mean').reset_index().set_index('gro')
    s_year = df.loc[year_s:].groupby('gro').apply(lambda ddf: (ddf.chg_mean + 1).cumprod().iloc[-1] - 1)
    df_year = s_year.rename('chg_mean').reset_index().set_index('gro')

    dx = pd.DataFrame(db_['quo_bins'].find({'date': the_date}, {'_id': 0, }, batch_size=1000000)).set_index('date').sort_index()
    dx['color'] = dx.bins.map(lambda x: 'red' if x > 0 else 'green')
    dx.loc[dx.bins == 0, 'color'] = 'black'

    fig_daily = _plot(df_today, dx.rename(columns={'daily': 'value'}), f'交易日：{the_date}',m='D')
    fig_weekly = _plot(df_week, dx.rename(columns={'weekly': 'value'}), f'当周：{d_w_s} ~ {the_date}',m='W')
    fig_monthly = _plot(df_month, dx.rename(columns={'monthly': 'value'}), f'当月：{d_m_s} ~ {the_date}',m='M')
    fig_yearly = _plot(df_year, dx.rename(columns={'yearly': 'value'}), f'今年：{year_s} ~ {the_date}',m='Y')

    context = {
        'trade_date': the_date,
        'fig_daily': fig_daily,
        'fig_weekly': fig_weekly,
        'fig_monthly': fig_monthly,
        'fig_yearly': fig_yearly,
    }
    return render(request, 'quotation/chg_dist.html', context)
