# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: views.py
@time: 2023/5/22 11:18
说明:
"""

from django.shortcuts import render
import pandas as pd
from Datas.db_client import get_client, get_client_U
from Utils.utils import trans_str_to_float64
from plotly import graph_objs as go

pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('expand_frame_repr', False)
pd.set_option('display.max_columns', None)
pd.set_option('display.precision', 14)


def _load_and_plot_style_factor(t_, text: str, begin_date: str = '2009-01-01'):
    df = pd.DataFrame(t_.find({}, {'_id': 0}, batch_size=100000)).set_index('date').sort_index()

    df = df.loc[begin_date:, ].dropna()
    plot_list = [
        go.Scatter(x=df.index, y=df.quantile_mid, name=f'quantile_mid'),
        go.Scatter(x=df.index, y=df.ln_ir, name=f'COEF_IR'),
        go.Scatter(x=df.index, y=df.ln_weight, mode='markers', name=f'weight', yaxis="y2", xaxis="x"),
        # go.Scatter(x=df.index, y=df.slope, name=f'IR_slop', yaxis="y2", xaxis="x"),
    ]
    s_ = df.iloc[-1]
    fig = go.Figure(data=plot_list,
                    layout={
                        'height': 1199,
                        "title": f"{text} STYLE FACTOR --->>> {s_.name} ~ WEIGHT:{s_.ln_weight}",
                        "font": {"size": 22, },
                        'legend': {'orientation': "v", 'yanchor': 'auto', 'xanchor': 'center', },
                        "yaxis": {"title": "COEF:mean/std", "zerolinecolor": "grey", "zerolinewidth": 3},
                        "yaxis2": {"title": "weight", "side": "right", "overlaying": "y"},
                    })
    return fig.to_html(full_html=False, include_plotlyjs=True)


def style_factor(request, begin_date='2009-01-01'):
    db = get_client(c_from='neo')['statistic']
    size = _load_and_plot_style_factor(db['style_size'], text='SIZE', begin_date=begin_date)
    vol = _load_and_plot_style_factor(db['style_vol'], text='VOL', begin_date=begin_date)

    context = {'size_v3': size, 'vol_v3': vol}
    return render(request, "mult_factor/risk_factor.html", context)


def mkt_cap_hist(request, the_date='latest'):
    c_ = get_client_U(m='r')
    t_ = c_.basic_wind.w_basic_financial
    if the_date == 'latest':
        the_date = next(t_.find({}, {'_id': 0, 'date': 1}).sort([('date', -1), ]).limit(1)).get('date')
    else:
        the_date = next(t_.find({'date': {'$lte': the_date}}, {'_id': 0, 'date': 1}).sort([('date', -1), ]).limit(1)).get('date')
    df = pd.DataFrame(t_.find({'date': the_date}, {'_id': 0, 'mkt_cap_ard': 1}, batch_size=1000000))

    trace0 = go.Histogram(x=df.mkt_cap_ard / (10 ** 8), histnorm="probability", cumulative={"enabled": True}, name='累计分布')
    trace1 = go.Histogram(x=df.mkt_cap_ard / (10 ** 8), histnorm="probability", name='市值分布')
    fig = go.Figure(data=[trace0, trace1],
                    layout={
                        'height': 1088,
                        "title": f"{the_date} 全市场 {df.shape[0]} 只票，市值分布直方图",
                        "font": {"size": 22, },
                        "xaxis": {"dtick": 20, "range": [0, 1000], "title": "市值（单位：亿元）", },
                        "yaxis": {"title": "分布占比", },
                        "barmode": "overlay",
                    })
    return render(request, "mult_factor/cap_dist.html",
                  {'date': the_date,
                   'fig': fig.to_html(full_html=False, include_plotlyjs=True)})


def weight(request, the_date='latest'):
    db = get_client(c_from='neo')
    t_ = db['stra_V3_1']['stra_weight']
    if the_date == 'latest':
        the_date = next(t_.find({}, {'_id': 0, 'date': 1}).sort([('date', -1), ]).limit(1)).get('date')
    else:
        the_date = next(t_.find({'date': {'$lte': the_date}}, {'_id': 0, 'date': 1}).sort([('date', -1), ]).limit(1)).get('date')
    df = trans_str_to_float64(pd.DataFrame(t_.find({'date': {'$lte': the_date}},
                                                   {'_id': 0, 'pool_num': 0, 'picked_num': 0, 'factors': 0, 'direction': 0},
                                                   batch_size=100000)),
                              exp_cols=['date', ]).set_index('date').sort_index()
    plot_list = []
    for col in df.columns.tolist():
        plot_list.append(go.Scatter(x=df.index, y=df[col], name=f'{col}'))

    fig = go.Figure(data=plot_list,
                    layout={
                        'height': 1199,
                        "title": f"ALPHA FACTORS WEIGHT LIST OF HISTORY, END TO {the_date}",
                        'legend': {'title': 'HISTORY ALPHA'},
                        "font": {"size": 22, },
                        "yaxis": {"title": "WEIGHT", "zerolinecolor": "grey", "zerolinewidth": 3},
                    })
    return render(request, template_name='mult_factor/weight.html',
                  context={'the_date': the_date,
                           'fig': fig.to_html(full_html=False, include_plotlyjs=True)})


ALPHA_FACTORS = {
    'value': ['F_B2P', 'F_E2P', 'F_S2P', 'F_EBIT2P', 'F_cfo2ev', ],
    'quality': ['F_ROE', 'F_ROA', 'F_EPS', 'F_LOAR', 'F_NI2S', 'F_GPM', 'F_C2E', 'F_cfo2roi', ],
    'growth': ['F_ebitGttm', 'F_NIGttm', 'F_SalesGttm', ],
    'momentum': ['F_ret_com', ],
}


def _p_cols(df: pd.DataFrame, key_cols: str, text: str, picked: str):
    """
    画图，IC累和 或者 IR
    :param df:
    :param key_cols:
    :param text:
    :param picked:
    :return:
    """
    plot_list = []
    for col in df.columns.tolist():
        plot_list.append(
            go.Scatter(x=df.index, y=df[col], name=f'{col}', )
        )
    fig = go.Figure(data=plot_list,
                    layout={
                        'height': 777,
                        "title": f"因子大类：{key_cols} ~ 今日选择：{picked}",
                        "font": {"size": 22, },
                        "yaxis": {"title": f"{text}", "zerolinecolor": "grey", "zerolinewidth": 3},
                    })
    return fig.to_html(full_html=False, include_plotlyjs=True)


def ic_ir(request, the_date='latest'):
    """
    IC_IR
    :param request:
    :param the_date:
    :return:
    """
    db = get_client(c_from='neo')
    t_ic = db['stra_V3_1']['stra_ics']
    t_ir = db['stra_V3_1']['stra_IR']

    if the_date == 'latest':
        the_date = next(t_ir.find({}, {'_id': 0, 'date': 1}).sort([('date', -1), ]).limit(1)).get('date')
    else:
        the_date = next(t_ir.find({'date': {'$lte': the_date}}, {'_id': 0, 'date': 1}).sort([('date', -1), ]).limit(1)).get('date')
    irs = pd.DataFrame(t_ir.find({'date': {'$lte': the_date}},
                                 {'_id': 0, })).set_index('date').sort_index()
    the_date = irs.iloc[-1].name

    ics = trans_str_to_float64(pd.DataFrame(t_ic.find({'date': {'$lte': the_date}}, {'_id': 0, })),
                               exp_cols=['date', ]).set_index('date').sort_index()

    ir = ics.mean(numeric_only=True) / ics.std(numeric_only=True)
    picks, figs = [], []
    for k, v in ALPHA_FACTORS.items():
        picked = ir[list(v)].idxmax()
        picks.append(picked)
        figs.append((
            _p_cols(ics[list(v)].sort_index().cumsum(), k, 'IC累和',  ),
            _p_cols(irs[list(v)], k, 'IR', picked)
        ))
    return render(request, template_name='mult_factor/ic_ir.html', context={'the_date': the_date,
                                                                            'picks': picks,
                                                                            'figs': figs})


def _plot_mono(df: pd.DataFrame, text: str):
    df1 = df.loc[df['size'] == 'size_0'].copy()
    df11 = df1.drop(columns=['size', 'SIZE_LOW', 'SIZE_2', 'SIZE_3', 'SIZE_4', 'SIZE_HIGH']).copy()
    ds1 = (df11 + 1).cumprod()

    plot_list = []
    for col in ds1.columns.tolist():
        plot_list.append(
            go.Scatter(x=ds1.index, y=ds1[col], name=f'{col}', )
        )
    date_s, date_e = ds1.index.min(), ds1.index.max()
    fig = go.Figure(data=plot_list,
                    layout={
                        'height': 1177,
                        "title": f"单调性检验(无成本累计净值)：{text}，期间：【{date_s} ~ {date_e}】",
                        "font": {"size": 22, },
                        "yaxis": {"title": "NET_VALUE CUM_PROD", "zerolinecolor": "red", "zerolinewidth": 3},
                    })
    # fig.show()

    df12 = df1[['SIZE_LOW', 'SIZE_2', 'SIZE_3', 'SIZE_4', 'SIZE_HIGH']].copy()
    df12.rename(columns={'SIZE_LOW': 'LOW', 'SIZE_2': '2', 'SIZE_3': '3', 'SIZE_4': '4', 'SIZE_HIGH': 'HIGH'}, inplace=True)
    ds12 = (df12 / 100000000).describe()
    trace0 = go.Heatmap(x=ds12.columns.to_list(),
                        y=ds12.index.to_list(),
                        z=ds12.values.tolist(),
                        text=ds12.map(lambda x: format(x, '.2f')).values.tolist(),
                        texttemplate="%{text}", zmin=ds12.loc['mean'].min(), zmax=ds12.loc['mean'].max())
    fig12 = go.Figure(
        data=[trace0],
        layout={
            # 'height': 888,
            "title": f"描述性统计：{text}分组之SIZE均值",
            "font": {"size": 22, },
            "xaxis": {"side": "top", },
        }
    )
    # fig12.show()

    df2 = df.loc[~(df['size'] == 'size_0')].dropna(axis=1).copy()
    ds2 = df2.groupby('size').apply(lambda dx: (dx + 1).cumprod())

    dd = ds2.groupby('size').apply(lambda dx: dx.iloc[-1])

    trace0 = go.Heatmap(x=dd.columns.to_list(),
                        y=['BIG', 'BIG-', 'MID', 'SMALL-', 'SMALL'],
                        z=dd.values.tolist(),
                        text=dd.map(lambda x: format(x, '.2f')).values.tolist(),
                        texttemplate="%{text}", zmin=dd.values.min(), zmax=dd.values.max())
    fig1 = go.Figure(
        data=[trace0],
        layout={
            'height': 888,
            "title": f"控制规模影响后，单调性趋势(无成本累计净值): {text}，期间：【{date_s} ~ {date_e}】",
            "font": {"size": 22, },
            "xaxis": {"side": "top", },
        }
    )
    # fig1.show()

    return (fig.to_html(full_html=False, include_plotlyjs=True),
            fig12.to_html(full_html=False, include_plotlyjs=True),
            fig1.to_html(full_html=False, include_plotlyjs=True))


def monotonic(request, factor: str, begin_date: str = '2009-01-01'):
    drt = True
    if factor == 'FC':
        factor_t = 'monotonic_fc'
        text = '融合阿尔法因子'
    elif factor == 'BLACK':
        factor_t = 'monotonic_blacklist'
        text = '黑名单过滤因子'
        drt = False
    elif factor == 'VOL':
        factor_t = 'monotonic_vol15'
        text = '风格(成交量)因子'
        drt = False
    else:
        raise Exception(f'传入因子参数出错...')

    t_factor = get_client(c_from='neo')['statistic'][factor_t]
    df = pd.DataFrame(t_factor.find({'date': {'$gte': begin_date}},
                                    {'_id': 0}, batch_size=100000)).set_index('date').sort_index()
    df.rename(columns={'CHG_LOW': 'LOW', 'CHG_2': '2', 'CHG_3': '3', 'CHG_4': '4', 'CHG_HIGH': 'HIGH'}, inplace=True)
    if drt:
        df['HML'] = df['HIGH'] - df['LOW']
    else:
        df['LMH'] = df['LOW'] - df['HIGH']

    f1, f11, f2 = _plot_mono(df, text)

    return render(request, template_name='mult_factor/monotonic.html', context={'date_s': begin_date,
                                                                                'text': text,
                                                                                'fig_all': f1,
                                                                                'fig_des': f11,
                                                                                'fig_size': f2})
