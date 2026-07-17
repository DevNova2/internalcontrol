# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: stat.py
@time: 2023/5/23 17:06
说明:
"""
import numpy as np
import pandas as pd


def stat_max(df_from, col='累计净值  (元)'):
    """循环取得截至当前的最大净值，增加字段 'max_value' """
    df = df_from.copy()
    max_return = 1  # 最大净值
    df['max_value'] = max_return
    for i in df.index:
        returns = df.loc[i, col]
        # 计算目前的最大净值
        if returns > max_return:
            max_return = returns
        df.loc[i, 'max_value'] = max_return
    return df


def layer_backtest(alpha_df, chg_df, col=None, group_num=5):
    """
    分层回测模块，两个DF有set_index(['date', 'code']
    :param alpha_df:
    :param chg_df:
    :param col: 指定的因子列名
    :param group_num:
    :return:
    """
    if col is None:
        raise Exception("没有指定因子名，怎么搞分层？")
    ASC = True if col in ["F_ret_com", 'mv_vol'] else False  # 这个因子反向用的
    alpha_df = alpha_df.copy()
    chg_df = chg_df.copy()
    date_range = np.unique([i[0] for i in alpha_df.index])
    groups = [[]] * group_num
    for d in range(1, date_range.size):
        # print(date_range[d])
        alpha_yesday = alpha_df.loc[date_range[d - 1]].sort_values(by=col, ascending=ASC)  # 前一天因子值
        chg_today = chg_df.loc[date_range[d]]  # 后一天涨跌幅
        each_group = alpha_yesday.shape[0] // group_num  # 每组有多少只票
        for i in range(0, group_num):
            group_stocks = alpha_yesday[i * each_group:(i + 1) * each_group].index.tolist()  # 找出这个分组的股票
            chg_stocks = chg_today.loc[group_stocks].chg.mean()  # 找出这些票的平均涨跌幅
            groups[i] = groups[i] + [chg_stocks]  # 将数据放入到容器中
    groups = pd.DataFrame(groups).T
    groups.index = date_range[1:]
    return groups
