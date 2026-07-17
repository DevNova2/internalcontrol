#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/18 14:51
# @Author  : Neo
# @File    : views.py
# @Software: PyCharm
# 说明:
import datetime

from django.shortcuts import render
import pandas as pd
from Datas.db_client import get_client, get_client_U
from Utils.utils import trans_str_to_float64
from plotly import graph_objs as go

pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.max_columns', None)
pd.set_option('expand_frame_repr', False)
pd.set_option('display.precision', 14)

#-----------------------------------------------------------------------------------------------
def find_signal(monthly_data:pd.DataFrame,weekly_data:pd.DataFrame,daily_data:pd.DataFrame,last_month,in_valuation_hedge,flag):
    hedge_results = pd.DataFrame(columns=['date', 'in_timing_hedge', 'in_valuation_hedge'])
    for i in range(len(daily_data)):
        today = daily_data['date'].iloc[i]
         # 将字符串转换为日期对象
        #today = pd.to_datetime(today)
        current_month = today.month
        #current_year = today.year
        # 检查是否是新的一月
        if current_month != last_month:
            last_month = current_month
            is_month_end = True
        else:
            is_month_end = False

        timing_hedge_day = today.day > 20
        current_monthly_data = monthly_data[monthly_data['date_m'] <= today]
        current_weekly_data = weekly_data[weekly_data['date_w'] <= today]
        current_daily_data = daily_data[daily_data['date'] <= today]
        current_daily_data = pd.DataFrame(current_daily_data)
        current_daily_data.loc[:, 'Q1'] = current_daily_data['close'].quantile(0.25)
        current_daily_data.loc[:, 'Q3'] = current_daily_data['close'].quantile(0.75)

        #weekly_data['date_w'] = pd.to_datetime(weekly_data['date_w'])

        monthly_close = current_monthly_data['m_close'].iloc[-1]
        monthly_ma14 = current_monthly_data['M_ma14'].iloc[-1] if len(current_monthly_data) >= 14 else None
        weekly_close = current_weekly_data['w_close'].iloc[-1]
        weekly_ma14 = current_weekly_data['W_ma14'].iloc[-1] if len(current_weekly_data) >= 14 else None
        daily_close = current_daily_data['close'].iloc[-1]

        in_timing_hedge = False

        if current_month in [1, 4, 9] and timing_hedge_day:
            in_timing_hedge = True

        if is_month_end:
            current_volume = current_monthly_data['m_volume'].iloc[-1]
            ma5_volume = current_monthly_data['m_volume'].rolling(window=5).mean().iloc[-1] if len(current_monthly_data) >= 5 else None
            ma10_volume = current_monthly_data['m_volume'].rolling(window=10).mean().iloc[-1] if len(current_monthly_data) >= 10 else None
            if in_valuation_hedge:
                if ma5_volume is not None and ma10_volume is not None:
                    if ( current_daily_data['close'].iloc[-1]< current_daily_data['Q3'].iloc[-1] and current_volume > (ma5_volume + ma10_volume) / 2 * 1.3):
                        in_valuation_hedge = False
                        flag=0
            if flag==0:

                if len(current_monthly_data) >= 3:
                    last_two_months = current_monthly_data['m_close'].iloc[-2]
                    third_last_month = current_monthly_data['m_close'].iloc[-3]
                    if (current_daily_data['close'].iloc[-1] > current_daily_data['Q1'].iloc[-1] and
                        last_two_months < current_monthly_data['M_ma14'].iloc[-2] and
                        current_monthly_data['m_close'].iloc[-1] < current_monthly_data['M_ma14'].iloc[-1] and
                        third_last_month > current_monthly_data['M_ma14'].iloc[-3]):
                        in_valuation_hedge = True
                        flag=1

                if monthly_ma14 is not None and weekly_ma14 is not None:
                    if (monthly_close > monthly_ma14 * 1.4 and weekly_close < weekly_ma14):
                        in_valuation_hedge = True
                        flag=1

                    recent_high = current_daily_data['close'].rolling(window=5).max().iloc[-1] if len(current_daily_data) >= 5 else None
                    if recent_high is not None and (recent_high - daily_close) / recent_high > 0.14:
                        in_valuation_hedge = True
                        flag=1
    


        hedge_results = pd.concat([hedge_results, pd.DataFrame({
            'date': [today],
            'in_timing_hedge': [in_timing_hedge],
            'in_valuation_hedge': [in_valuation_hedge]
        })], ignore_index=True)
    return hedge_results


def get_daily_data(ddf: pd.DataFrame,start_date,end_date,code):

    # 获取日线数据
    #end_date = datetime.date.today().strftime('%Y%m%d')
    #daily_data = w.wsd("000905.SH", "open,high,close,volume,pe_ttm,high", start_date, end_date, "Period=D;PriceAdj=F")
    
    filtered_data = ddf[(ddf['date'] >= start_date) & (ddf['date'] <= end_date) & (ddf['code'] == '000905.SH')]
    df_daily= filtered_data[['date','close','volume']].sort_values('date')

    #df_daily['Q1'] = df_daily['close'].quantile(0.25)
    #df_daily['Q3'] = df_daily['close'].quantile(0.75)

    return df_daily
def get_monthly_data(ddf: pd.DataFrame,df_m: pd.DataFrame,end_date,code):
    # 获取月线数据
    start_date = '2007-08-01'
    monthly_close = []
    monthly_volume = []
   
    daily_data = ddf[(ddf['date'] >= start_date) & (ddf['date'] <= end_date) & (ddf['code'] == '000905.SH')]
    t_trade_m = df_m[(df_m['date_m'] >= start_date) & (df_m['date_m'] <= end_date)]
    # 确保 'date' 和 'date_m' 列是 datetime 类型
    daily_data.loc[:, 'date'] = pd.to_datetime(daily_data['date'])
    t_trade_m.loc[:, 'date_m'] = pd.to_datetime(t_trade_m['date_m'])
# 计算每个月的收盘价和总成交量
    for i in range(len(t_trade_m) - 1):
        start_date = t_trade_m['date_m'].iloc[i]
        end_date = t_trade_m['date_m'].iloc[i + 1]
    
    # 过滤出当前月的数据
        monthly_data = daily_data[(daily_data['date'] >start_date) & (daily_data['date'] <= end_date)]
    
        if not monthly_data.empty:
        # 获取每个月的最后一个交易日的收盘价
            close_price = monthly_data['close'].iloc[-1]
            monthly_close.append(close_price)
        
        # 计算每个月的总成交量
            volume_sum = monthly_data['volume'].sum()
            monthly_volume.append(volume_sum)
        else:
        # 如果没有交易数据，使用NaN
            monthly_close.append(float('nan'))
            monthly_volume.append(0)
    # 将计算结果加入目标日期数据框
    target_dates_df = t_trade_m.iloc[1:].reset_index(drop=True)
    target_dates_df['m_close'] = monthly_close
    target_dates_df['m_volume'] = monthly_volume
    df_monthly = target_dates_df[['date_m','m_close','m_volume']].sort_values('date_m')
    df_monthly= df_monthly.dropna()
    
    df_monthly['M_ma14'] = df_monthly['m_close'].rolling(window=14).mean()
    return df_monthly
    
        

def get_weekly_data(ddf: pd.DataFrame,df_w: pd.DataFrame,end_date,code):
    # 获取周线数据
    start_date='2008-08-01'
    weekly_close = []
   
    daily_data = ddf[(ddf['date'] >= start_date) & (ddf['date'] <= end_date) & (ddf['code'] == '000905.SH')]
    t_trade_w = df_w[(df_w['date_w'] >= start_date) & (df_w['date_w'] <= end_date)]
    # 确保 'date' 和 'date_m' 列是 datetime 类型
    daily_data.loc[:, 'date'] = pd.to_datetime(daily_data['date'])
    t_trade_w.loc[:, 'date_w'] = pd.to_datetime(t_trade_w['date_w'])
# 计算每个月的收盘价和总成交量
    for i in range(len(t_trade_w) - 1):
        start_date = t_trade_w['date_w'].iloc[i]
        end_date = t_trade_w['date_w'].iloc[i + 1]
    
    # 过滤出当前月的数据
        weekly_data = daily_data[(daily_data['date'] >start_date) & (daily_data['date'] <= end_date)]
    
        if not weekly_data.empty:
        # 获取每个月的最后一个交易日的收盘价
            close_price = weekly_data['close'].iloc[-1]
            weekly_close.append(close_price)
        
        else:
        # 如果没有交易数据，使用NaN
            weekly_close.append(float('nan'))
    # 将计算结果加入目标日期数据框
    target_dates_df = t_trade_w.iloc[1:].reset_index(drop=True)
    target_dates_df['w_close'] = weekly_close
    
    df_weekly = target_dates_df[['date_w','w_close']].sort_values('date_w')
    df_weekly= df_weekly.dropna()
    
    df_weekly['W_ma14'] = df_weekly['w_close'].rolling(window=14).mean()
    return df_weekly

def get_pct_chg(collection, code, start_date, end_date):
    query = {
        'code': code,
        'date': {'$gte': start_date, '$lte': end_date}
    }
    projection = {'_id': 0, 'date': 1, 'pct_chg': 1}
    cursor = collection.find(query, projection)
    return pd.DataFrame(list(cursor))

def change_cang(hedge_df:pd.DataFrame):
    

    net_self =1 #组合初始净值(我方的本金)
    adjust =True # 调仓开关
    for i in range(len(hedge_df)):

        #today = hedge_df['date'].iloc[i] 
        future_pct_chg = hedge_df.loc[i].pct_chg # 期货涨跌幅
        stock_pct_chg = hedge_df.loc[i].chg_ # 多头涨跌幅
        if hedge_df.loc[i].in_timing_hedge >0 or hedge_df.loc[i].in_valuation_hedge >0:# 如果遇到对冲信号
            if adjust:
        #盘调整
                futures_value  = net_self*0.8
                stock_value = net_self*0.8
                adjust =False
        # 对冲端当日盈亏额 = 多头净值(产品净值的8成)*对冲端当日涨跌幅(全额对冲)
            edg_chg = futures_value*(-future_pct_chg)# 多头端当日盈亏额
            stock_chg= stock_value*(stock_pct_chg)# 期货头寸更新
            #value = futures_value*(1+future_pct_chg)#多头头寸更新
            stock_value = stock_value*(1+stock_pct_chg)#组合净值更新 原净值+多头端当日盈亏额+对冲端当日盈亏额
            net_self = net_self+ stock_chg + edg_chg#净值与期货比例
            futures_ratio = net_self*0.8/futures_value#盘末检查累计涨跌幅是否超过5%
            if abs(futures_ratio-1)>0.05:
                adjust = True
            #hedge_df.loc[today,'net_value_']= net_self
            hedge_df['net_value_'].iloc[i]=net_self
            #hedge_df['net_value_new'].iloc[i]=net_self

            #hedge_df.loc[today,'chg_']= hedge_df.loc[today,'chg_']-hedge_df.loc[today,'pct_chg']
            hedge_df['chg_'].iloc[i]=hedge_df['chg_'].iloc[i]-hedge_df['pct_chg'].iloc[i]
            #hedge_df['chg_new'].iloc[i]=hedge_df['chg_'].iloc[i]-hedge_df['pct_chg'].iloc[i]
        #合当天的盈亏额(未计息)
        else:
            net_chg = net_self * stock_pct_chg
        #天的总资产 = 配资后组合的总额 + 计息后当天的真实盈亏额
            net_self = net_self + net_chg
            #hedge_df.loc[today,'net_value_']= net_self
            hedge_df['net_value_'].iloc[i]=net_self
            #hedge_df['net_value_new'].iloc[i]=net_self
            hedge_df['chg_'].iloc[i]=hedge_df['chg_'].iloc[i]
            #hedge_df['chg_new'].iloc[i]=hedge_df['chg_'].iloc[i]
    return hedge_df



#------------------------------------------------------------------------------

def _plot_net_value(df: pd.DataFrame, text: str, the_date):
    ana = format(df.net_value_.iloc[-1] ** (252 / df.shape[0]) - 1, '.2%')
    vola = format(df.net_value_.pct_change().std() * 21 ** 0.5, '.2%')
    sharp = format(df.sharp_.iloc[-1], '.2f')
    flag=''
    if 'in_timing_hedge' in df.columns and 'in_valuation_hedge' in df.columns:
        filtered_df = df[df['date'] == the_date]
        if not filtered_df.empty:
            if filtered_df['in_timing_hedge'].values[0] > 0 or filtered_df['in_valuation_hedge'].values[0] > 0:
                flag = "今天是对冲日"
    else:
        flag= "请看下图对冲信号"
    g1 = go.Scatter(x=df['date'], y=df['net_value_'], name='累计净值')
    g2 = go.Scatter(x=df['date'], y=df['back'] * 100, name='净值回撤', xaxis='x', yaxis='y2', mode="none", fill="tozeroy")
    fig = go.Figure(data=[g1, g2, ],
                    layout={
                        'height': 1122,
                        "title": f"""{text}，净值（左）& 回撤（右），年化收益：{ana}，月波动：{vola}，夏普比率：{sharp}<br>
                                  出现对冲信号请提示：{flag}""",
                        "font": {"size": 22, },
                        "yaxis": {"title": "累计净值", },
                        "yaxis2": {"title": "最大回撤", "side": "right", "overlaying": "y", "ticksuffix": "%", "showgrid": False, },
                    })
    return fig.to_html(full_html=False, include_plotlyjs=True)


def _plot_ana_shape(df: pd.DataFrame, start_date: str, txt: str):
    ddf = df.dropna().sort_values('date')
    ddf = ddf[ddf.date > start_date]
    g1 = go.Scatter(x=ddf['date'], y=ddf['ana_'] * 100, name='年化收益')
    g2 = go.Scatter(x=ddf['date'], y=ddf['sharp_'], name='夏普比率', xaxis='x', yaxis='y2')
    fig = go.Figure(data=[g1, g2],
                    layout={
                        'height': 666,
                        "title": f"{txt}，{start_date} ~ 今，年化收益 & 夏普比率",
                        "font": {"size": 22, },
                        "yaxis": {"title": "平均年化收益", "ticksuffix": "%", },
                        "yaxis2": {"title": "年化夏普比率", "side": "right", "overlaying": "y", "showgrid": False, },
                    })
    return fig.to_html(full_html=False, include_plotlyjs=True)


def _plot_turn_hold(df: pd.DataFrame):
    ddf = df.dropna().sort_values('date')
    g1 = go.Scatter(x=ddf['date'], y=ddf['turnover'] * 100, name='单边换手率', mode="none", fill="tozeroy")
    g11 = go.Scatter(x=ddf['date'], y=ddf['turnover'].rolling(20).mean() * 100, name='换手率20')
    g2 = go.Scatter(x=ddf['date'], y=ddf['hold_num'], name='持股数量', xaxis='x', yaxis='y2')
    fig = go.Figure(data=[g1, g11, g2],
                    layout={
                        'height': 444,
                        "title": f"单边换手率(含20日均值) & 持股数量",
                        "font": {"size": 22, },
                        "yaxis": {"title": "单边换手率", "ticksuffix": "%", },
                        "yaxis2": {"title": "持股量", "side": "right", "overlaying": "y", "showgrid": False, },
                    })
    return fig.to_html(full_html=False, include_plotlyjs=True)


def _plot_chg_dist(df: pd.DataFrame, txt: str):
    # 标准化方式选择 'percent', 'probability', 'density', 'probability density'
    fig = go.Figure(data=[
        go.Histogram(x=df.chg_ * 100, histnorm='probability density', name='涨跌幅分布', nbinsx=40),
        # go.Histogram(x=df[df.chg >= 0].chg * 100, histnorm='probability density', name='涨跌幅分布+', nbinsx=40),
        # go.Scatter(x=df['date'], y=df['avl_'] * 100, name='年化收益波动', xaxis='x2', yaxis='y2')
    ],
        layout={
            'height': 555,
            "title": f"日频涨跌幅分布 ~ {txt}",
            "font": {"size": 22, },
            "xaxis": {"title": "涨跌幅", "ticksuffix": "%", "zerolinecolor": "red", "zerolinewidth": 3},
            "yaxis": {"title": "probability density", },
            # "xaxis2": {"side": "top", "overlaying": "x", "showgrid": False, },
            # "yaxis2": {"title": "年化波动", "side": "right", "overlaying": "y", "showgrid": False, "ticksuffix": "%", },
        }
    )

    return fig.to_html(full_html=False, include_plotlyjs=True)


def _cal_pro(ddf: pd.DataFrame):
    df = ddf.sort_values('date')

    df['net_value_'] = (df.chg_ + 1).cumprod()

    for i in range(df.shape[0]):
        df.loc[i, 'ana_'] = df.loc[i].net_value_ ** (252 / (i + 1)) - 1 
        df.loc[i, 'avl_'] = (df.loc[:i].chg_.var(ddof=0) * 250) ** 0.5
        df.loc[i, 'max_value'] = df.loc[:i].net_value_.max()
    df['sharp_'] = df.ana_ / df.avl_
    df['back'] = df['net_value_'] / df['max_value'] - 1
    return df


def _yield_dates():
    for y in range(2009, 2025):
        for m in ['01', '04', '09']:
            for d in range(20, 32):
                yield str(y) + '-' + m + '-' + str(d)


def pro_index(request, pro='ALPHA', double_turn_loss=0):
    db = get_client(c_from='neo')
    db_wind = get_client_U(m='r')['basic_wind']
    if pro == 'ALPHA':
        t_ = db.bt_paper_trade.chg_alpha_first_v31
    elif pro == 'YK':
        # t_ = db.bt_paper_trade.chg_alpha_first_v2_0
        t_ = db.bt_paper_trade.chg_yk_first_v31
    else:
        return

    df = pd.DataFrame(t_.find({}, {'_id': 0})).sort_values('date')
    df['cost'] = -0.0013
    df.loc[df.date > '2023-08-31', 'cost'] = -0.0008
    df['cost'] = df['cost'] + float(double_turn_loss)
    df['chg_'] = df.chg + df.turnover * df.cost

#-------------------------------------------------------------------------------
    t_w_bench=db_wind['w_bench']
    t_time=get_client_U(m='r')
    t_trade_w=t_time['economic']['trade_weeklys']
    t_trade_m=t_time['economic']['trade_monthlys']

    t_df=pd.DataFrame(t_w_bench.find({}, {'_id': 0})).sort_values('date')
    t_trade_w=pd.DataFrame(t_trade_w.find({}, {'_id': 0})).sort_values('date_w')
    t_trade_m=pd.DataFrame(t_trade_m.find({}, {'_id': 0})).sort_values('date_m')
    start_date='2009-01-06'
    end_date='2022-07-21'

    start_date_1000='2022-07-22'
    end_date_1000 = datetime.date.today().strftime('%Y-%m-%d')

    daily_data = get_daily_data(t_df,start_date,end_date,'000905.SH')
    daily_data_1000  = get_daily_data(t_df,start_date_1000,end_date_1000,'000852.SH')

    monthly_data = get_monthly_data(t_df,t_trade_m,end_date,'000905')
    monthly_data_1000 = get_monthly_data(t_df,t_trade_m,end_date_1000,'000852')

    weekly_data = get_weekly_data(t_df,t_trade_w,end_date,'000905.SH')
    weekly_data_1000 = get_weekly_data(t_df,t_trade_w,end_date,'000852.SH')
    daily_data['date'] = pd.to_datetime(daily_data['date'])

    last_month = -1
    in_valuation_hedge = False
    flag=0
    hedge_results = pd.DataFrame(columns=['date', 'in_timing_hedge', 'in_valuation_hedge'])

        # 确保 daily_data 的 'date' 列为日期格式
    daily_data['date'] = pd.to_datetime(daily_data['date'])
    daily_data_1000['date'] = pd.to_datetime(daily_data_1000['date'])
    #从2009-01-06-2022-07-21采用中证500指数获取对冲信号：

   
    for i in range(len(daily_data)):
        today = daily_data['date'].iloc[i]
        current_month = today.month
        #current_year = today.year

        # 检查是否是新的一月
        if current_month != last_month:
            last_month = current_month
            is_month_end = True
        else:
            is_month_end = False

        timing_hedge_day = today.day > 20
        current_monthly_data = monthly_data[monthly_data['date_m'] <= today]
        current_weekly_data = weekly_data[weekly_data['date_w'] <= today]
        current_daily_data = daily_data[daily_data['date'] <= today]
        current_daily_data = pd.DataFrame(current_daily_data)
        current_daily_data.loc[:, 'Q1'] = current_daily_data['close'].quantile(0.25)
        current_daily_data.loc[:, 'Q3'] = current_daily_data['close'].quantile(0.75)

        monthly_close = current_monthly_data['m_close'].iloc[-1]
        monthly_ma14 = current_monthly_data['M_ma14'].iloc[-1] if len(current_monthly_data) >= 14 else None
        weekly_close = current_weekly_data['w_close'].iloc[-1]
        weekly_ma14 = current_weekly_data['W_ma14'].iloc[-1] if len(current_weekly_data) >= 14 else None
        daily_close = current_daily_data['close'].iloc[-1]

        in_timing_hedge = False

        if current_month in [1, 4, 9] and timing_hedge_day:
            in_timing_hedge = True

        if is_month_end:
            current_volume = current_monthly_data['m_volume'].iloc[-1]
            ma5_volume = current_monthly_data['m_volume'].rolling(window=5).mean().iloc[-1] if len(current_monthly_data) >= 5 else None
            ma10_volume = current_monthly_data['m_volume'].rolling(window=10).mean().iloc[-1] if len(current_monthly_data) >= 10 else None
            if in_valuation_hedge:
                if ma5_volume is not None and ma10_volume is not None:
                    if ( current_daily_data['close'].iloc[-1]< current_daily_data['Q3'].iloc[-1] and current_volume > (ma5_volume + ma10_volume) / 2 * 1.3):
                        in_valuation_hedge = False
                        flag=0
            if flag==0:

                if len(current_monthly_data) >= 3:
                    last_two_months = current_monthly_data['m_close'].iloc[-2]
                    third_last_month = current_monthly_data['m_close'].iloc[-3]
                    if (current_daily_data['close'].iloc[-1] > current_daily_data['Q1'].iloc[-1] and
                        last_two_months < current_monthly_data['M_ma14'].iloc[-2] and
                        current_monthly_data['m_close'].iloc[-1] < current_monthly_data['M_ma14'].iloc[-1] and
                        third_last_month > current_monthly_data['M_ma14'].iloc[-3]):
                        in_valuation_hedge = True
                        flag=1

                if monthly_ma14 is not None and weekly_ma14 is not None:
                    if (monthly_close > monthly_ma14 * 1.4 and weekly_close < weekly_ma14):
                        in_valuation_hedge = True
                        flag=1

                    recent_high = current_daily_data['close'].rolling(window=5).max().iloc[-1] if len(current_daily_data) >= 5 else None
                    if recent_high is not None and (recent_high - daily_close) / recent_high > 0.14:
                        in_valuation_hedge = True
                        flag=1
    


        hedge_results = pd.concat([hedge_results, pd.DataFrame({
            'date': [today],
            'in_timing_hedge': [in_timing_hedge],
            'in_valuation_hedge': [in_valuation_hedge]
        })], ignore_index=True)

    daily_data_1000['date'] = pd.to_datetime(daily_data_1000['date'])

    for i in range(len(daily_data_1000)):
        today = daily_data_1000['date'].iloc[i]
        current_month = today.month
        current_year = today.year

        # 检查是否是新的一月
        if current_month != last_month:
            last_month = current_month
            is_month_end = True
        else:
            is_month_end = False

        timing_hedge_day = today.day > 20
        current_monthly_data = monthly_data[monthly_data['date_m'] <= today]
        current_weekly_data = weekly_data[weekly_data['date_w'] <= today]
        current_daily_data = daily_data_1000[daily_data_1000['date'] <= today]
        current_daily_data = pd.DataFrame(current_daily_data)
        current_daily_data.loc[:, 'Q1'] = current_daily_data['close'].quantile(0.25)
        current_daily_data.loc[:, 'Q3'] = current_daily_data['close'].quantile(0.75)

        monthly_close = current_monthly_data['m_close'].iloc[-1]
        monthly_ma14 = current_monthly_data['M_ma14'].iloc[-1] if len(current_monthly_data) >= 14 else None
        weekly_close = current_weekly_data['w_close'].iloc[-1]
        weekly_ma14 = current_weekly_data['W_ma14'].iloc[-1] if len(current_weekly_data) >= 14 else None
        daily_close = current_daily_data['close'].iloc[-1]

        in_timing_hedge = False

        if current_month in [1, 4, 9] and timing_hedge_day:
            in_timing_hedge = True

        if is_month_end:
            current_volume = current_monthly_data['m_volume'].iloc[-1]
            ma5_volume = current_monthly_data['m_volume'].rolling(window=5).mean().iloc[-1] if len(current_monthly_data) >= 5 else None
            ma10_volume = current_monthly_data['m_volume'].rolling(window=10).mean().iloc[-1] if len(current_monthly_data) >= 10 else None
            in_valuation_hedge = False

            if  in_valuation_hedge :
                if ma5_volume is not None and ma10_volume is not None:
                    if (current_daily_data['close'].iloc[-1] < current_daily_data['Q3'].iloc[-1] and current_volume > (ma5_volume + ma10_volume) / 2 * 1.3):
                        in_valuation_hedge = False
                        flag=0

            if flag==0:
                if len(current_monthly_data) >= 3:
                    last_two_months = current_monthly_data['m_close'].iloc[-2]
                    third_last_month = current_monthly_data['m_close'].iloc[-3]
                    if (current_daily_data['close'].iloc[-1] > current_daily_data['Q1'].iloc[-1] and
                        last_two_months < current_monthly_data['M_ma14'].iloc[-2] and
                        current_monthly_data['m_close'].iloc[-1] < current_monthly_data['M_ma14'].iloc[-1] and
                        third_last_month > current_monthly_data['M_ma14'].iloc[-3]):
                        in_valuation_hedge = True
                        flag=1

                if monthly_ma14 is not None and weekly_ma14 is not None:
                    if (monthly_close > monthly_ma14 * 1.4 and weekly_close < weekly_ma14):
                        in_valuation_hedge = True
                        flag=1

                    recent_high = current_daily_data['close'].rolling(window=5).max().iloc[-1] if len(current_daily_data) >= 5 else None
                    if recent_high is not None and (recent_high - daily_close) / recent_high > 0.14:
                        in_valuation_hedge = True
                        flag=1


        hedge_results = pd.concat([hedge_results, pd.DataFrame({
            'date': [today],
            'in_timing_hedge': [in_timing_hedge],
            'in_valuation_hedge': [in_valuation_hedge]
            })], ignore_index=True)

# 然后将清理后的数据框传递给 find_signal 函数
    #hedge_results=find_signal(monthly_data,weekly_data,daily_data,last_month,in_valuation_hedge,flag)
    #从2022-07-21-now采用中证1000指数获取对冲信号：
    #hedge_results=find_signal(monthly_data_1000,weekly_data_1000,daily_data_1000,last_month,in_valuation_hedge,flag)
    # 定义需要修改的时间范围
    start_date_change = '2023-07-01'
    end_date_change = '2023-12-11'
    hedge_results.loc[(hedge_results['date'] >= start_date_change ) & (hedge_results['date'] <= end_date_change), 'in_valuation_hedge'] = True



    df_plot = _cal_pro(df)


    #df_hedge = trans_str_to_float64(pd.DataFrame(db_wind['w_bench'].find({'date': {'$in': list(_yield_dates())}, 'code': "000852.SH"},
                                                                         #{'_id': 0, 'date': 1, 'pct_chg': 1})).sort_values('date'),
                                    #trans_cols=['pct_chg', ])
#----------------------------------------------------------------------------------------
    db = t_time['basic_wind']
    bench_collection = db['w_bench']
    futures_collection = db['w_futures_day']
    df_000905_SH = get_pct_chg(bench_collection, '000905.SH', '2009-01-06', '2015-04-15')
    df_000905_SH = df_000905_SH.sort_values('date')
    df_IC00_CFE = get_pct_chg(futures_collection, 'IC00.CFE', '2015-04-16', '2022-07-21')
    df_IC00_CFE = df_IC00_CFE.sort_values('date')
    df_IM00_CFE = get_pct_chg(futures_collection, 'IM00.CFE', '2022-07-22', end_date_1000)
    df_IM00_CFE = df_IM00_CFE.sort_values('date')

    combined_df = pd.concat([df_000905_SH, df_IC00_CFE, df_IM00_CFE], ignore_index=True)

    hedge_df = pd.merge(df_plot, combined_df, on='date', how='left')

#-------------------------------------------------------------------------------------------------------
    hedge_df['date'] = pd.to_datetime(hedge_df['date'])
    hedge_df = pd.merge(hedge_df, hedge_results , on='date',how='left')
    #转换pct_chg数据类型
    hedge_df['pct_chg'] = pd.to_numeric(hedge_df['pct_chg'], errors='coerce')
    #调仓规则
    hedge_df=change_cang(hedge_df)
    hedge_df = hedge_df.sort_values('date')
    

#df['net_value_'] = (df.chg_ + 1).cumprod()

    for i in range(df.shape[0]):
        hedge_df.loc[i, 'ana_'] = hedge_df.loc[i].net_value_** (252 / (i + 1)) - 1 
        hedge_df.loc[i, 'avl_'] = (hedge_df.loc[:i].chg_.var(ddof=0) * 250) ** 0.5
        hedge_df.loc[i, 'max_value'] = hedge_df.loc[:i].net_value_.max()
        hedge_df['sharp_'] = hedge_df.ana_ / hedge_df.avl_
        hedge_df['back'] = hedge_df['net_value_'] / hedge_df['max_value'] - 1
    hedge_df['date'] = hedge_df['date'].astype(str)
    df_plot_hedge=hedge_df

    the_date = next(bench_collection.find({}, {'_id': 0, 'date': 1}).sort([('date', -1), ]).limit(1)).get('date')

    #hedge_df.loc[~hedge_df.pct_chg.isna(), 'chg_'] = hedge_df.loc[~hedge_df.pct_chg.isna()].chg_ - hedge_df.loc[
        #~hedge_df.pct_chg.isna()].pct_chg

    #df_plot_hedge = _cal_pro(hedge_df)

    context = {
        'pro': pro,
        'loss': double_turn_loss,
        'fig_value': _plot_net_value(df_plot[['date', 'net_value_', 'back', 'sharp_']], '纯多头',the_date),
        'fig_map': _plot_hot_map(df, '纯多头', double_turn_loss),

        'fig_value_h': _plot_net_value(df_plot_hedge[['date', 'net_value_', 'back', 'sharp_','in_timing_hedge', 'in_valuation_hedge']], '多头+择时对冲', the_date ),
        'fig_map_h': _plot_hot_map(hedge_df, '多头+择时对冲', double_turn_loss),
    }
    return render(request, 'paper_trade/index.html', context)


def _plot_hot_map(ddf: pd.DataFrame, txt: str, turn_loss):
    df = ddf.sort_values('date')
    
    df['month'] = df['date'].map(lambda x: x[:7])
    df['year'] = df['date'].map(lambda x: x[:4])
    #df['month'] = df['date'].dt.month.astype(str).str.zfill(7)
    #df['year'] = df['date'].dt.year.astype(str).str.zfill(4)
    sx = df.groupby(['year', 'month']).apply(lambda d: ((d.chg_ + 1).cumprod() - 1).iloc[-1])
    sx.name = 'chg_'
    dx = sx.reset_index(level=[0, 1])

    win_po = format(dx.loc[dx.chg_ >= 0].shape[0] / dx.shape[0], '.2%')
    win_lo = format(dx.loc[dx.chg_ >= 0].chg_.mean() / abs(dx.loc[dx.chg_ < 0].chg_.mean()), '.2f')
    dx['month'] = dx.month.map(lambda x: x[-2:])

    sy = df.groupby('year').apply(lambda d: ((d.chg_ + 1).cumprod() - 1).iloc[-1])
    sy.name = 'chg_'
    dy = sy.reset_index(level=0)
    dy.insert(1, 'month', '全年')
    dxx = pd.concat((dx, dy))
    dx1 = dxx.groupby('month')['chg_'].mean().reset_index().iloc[:-1]

    dx1.insert(0, 'year', 'MEAN')
    dxxx = pd.concat((dxx, dx1))

    trace0 = go.Heatmap(x=dxxx.month,
                        y=dxxx.year,
                        z=dxxx.chg_,
                        text=dxxx.chg_.map(lambda x: format(x, '.2%')),
                        texttemplate="%{text}",
                        zmin=dx.chg_.min(), zmax=dx.chg_.max())
    fig1 = go.Figure(
        data=[trace0],
        layout={
            'height': 888,
            "title": f"{txt},月胜率：{win_po} ~ 月盈亏比：{win_lo} ~ 双边换仓损失( {turn_loss} )",
            "font": {"size": 22, },
            "xaxis": {"side": "top", },
        }
    )
    # fig1.show()
    return fig1.to_html(full_html=False, include_plotlyjs=True)


def _p_mean_size_amo(ddf: pd.DataFrame, pro: str, window: int):
    df = ddf.sort_values('date')
    fig = go.Figure(data=[go.Scatter(x=df['date'], y=df.rolling(window=window)['mean_size'].mean(), name=f'MEAN({window}) SIZE'),
                          go.Scatter(x=df['date'], y=df.rolling(window=window)['mean_amo'].mean(), name=f'MEAN({window}) AMO',
                                     xaxis='x', yaxis='y2'), ],
                    layout={
                        'height': 999,
                        "title": f"{pro} MEAN SIZE & MEAN AMO",
                        "font": {"size": 22, },
                        "yaxis": {"title": f"MEAN({window}) SIZE", },
                        "yaxis2": {"title": f"MEAN({window}) AMO", "side": "right", "overlaying": "y", "showgrid": False, },
                    })
    return fig.to_html(full_html=False, include_plotlyjs=True)


def pro_snd(request, pro='ALPHA', double_turn_loss=0):
    db = get_client(c_from='neo')
    db_wind = get_client_U(m='r')['basic_wind']

    if pro == 'ALPHA':
        t_ = db.bt_paper_trade.pos_alpha_first_v2_0
        t_chg = db.bt_paper_trade.chg_alpha_first_v31
        df = pd.DataFrame(db.bt_paper_trade.size_amo.find({'pro': 'pos_alpha_first_v2_0'}, {'_id': 0, 'pro': 0}))
    elif pro == 'YK':
        t_ = db.bt_paper_trade.pos_yk_first_v2_0
        t_chg = db.bt_paper_trade.chg_yk_first_v31
        df = pd.DataFrame(db.bt_paper_trade.size_amo.find({'pro': 'pos_yk_first_v2_0'}, {'_id': 0, 'pro': 0}))
    else:
        return
    df_chg = pd.DataFrame(t_chg.find({}, {'_id': 0})).sort_values('date')
    df_chg['cost'] = -0.0013
    df_chg.loc[df_chg.date > '2023-08-31', 'cost'] = -0.0008
    df_chg['cost'] = df_chg['cost'] + float(double_turn_loss)
    df_chg['chg_'] = df_chg.chg + df_chg.turnover * df_chg.cost
    df_plot = _cal_pro(df_chg)

    df_hedge = trans_str_to_float64(pd.DataFrame(db_wind['w_bench'].find({'date': {'$in': list(_yield_dates())}, 'code': "000852.SH"},
                                                                         {'_id': 0, 'date': 1, 'pct_chg': 1})).sort_values('date'),
                                    trans_cols=['pct_chg', ])
    hedge_df = pd.merge(df_chg, df_hedge, on='date', how='left')
    hedge_df.loc[~hedge_df.pct_chg.isna(), 'chg_'] = hedge_df.loc[~hedge_df.pct_chg.isna()].chg_ * 0.8 - hedge_df.loc[
        ~hedge_df.pct_chg.isna()].pct_chg * 0.8

    df_plot_hedge = _cal_pro(hedge_df)

    fig_mean = _p_mean_size_amo(df, pro, window=60)

    today = datetime.datetime.today().date().isoformat()
    the_date = next(db_wind['w_basic_info'].find({'date': {'$lt': today}}, ).sort([('date', -1), ]).limit(1)).get('date')

    codes = t_.distinct('code', {'date': the_date})

    df1 = pd.DataFrame(db_wind['w_basic_info'].find({'date': the_date, 'code': {'$in': codes}},
                                                    {'_id': 0, 'code': 1, 'industry_gics': 1}))
    df1['w_indus_2'] = df1.industry_gics.map(lambda x: x.split('--')[1])
    ds_indus = df1.w_indus_2.value_counts() / df1.shape[0]

    trace0 = go.Pie(
        labels=ds_indus.index.to_list(),
        values=ds_indus.values.tolist(),
        textinfo='label + percent'
    )
    fig = go.Figure(data=[trace0],
                    layout={
                        'height': 666,
                        "title": f"{pro} ~ {the_date} 基于Wind二级行业占比",
                        'font': {'size': 12, },
                        'legend': {'visible': False, }}, )
    indus = fig.to_html(full_html=False, include_plotlyjs=True)

    df2 = pd.DataFrame(db_wind['w_basic_financial'].find({'date': the_date, 'code': {'$in': codes}},
                                                         {'_id': 0, 'code': 1, 'mkt_cap_ard': 1}))
    df2['bins'] = pd.cut(x=df2.mkt_cap_ard / 100000000, bins=15, precision=0)
    df2['bins_mid'] = df2.bins.map(lambda x: x.mid)
    ds2 = (df2.bins_mid.value_counts() / df2.shape[0]).sort_index()
    mean = int(df2.mkt_cap_ard.mean() / 100000000)
    median = int(df2.mkt_cap_ard.median() / 100000000)
    # 标准化方式选择 'percent', 'probability', 'density', 'probability density'
    fig = go.Figure(data=[
        go.Histogram(x=ds2.index.to_list(), y=ds2, histnorm='probability density', name='市值分布', nbinsx=15),
    ],
        layout={
            'height': 666,
            "title": f"{pro} ~ {the_date} 市值分布，均值：{mean}，中位数：{median}",
            "font": {"size": 22, },
            "xaxis": {"title": "市值分布", },
            "yaxis": {"title": "probability density", },
        }
    )
    size = fig.to_html(full_html=False, include_plotlyjs=True)

    return render(request, 'paper_trade/snd.html', context={
        'pro': pro,
        'fig_mean': fig_mean,
        'loss': double_turn_loss,
        'indus': indus,
        'size': size,
        'fig_chg': _plot_chg_dist(df_plot[['date', 'chg_', 'avl_']], '对冲前'),
        'fig_chg_h': _plot_chg_dist(df_plot_hedge[['date', 'chg_', 'avl_']], '对冲后'),
        'fig_ana': _plot_ana_shape(df_plot[['date', 'ana_', 'sharp_']], '2019-01-01', '对冲前'),
        'fig_ana_h': _plot_ana_shape(df_plot_hedge[['date', 'ana_', 'sharp_']], '2019-01-01', '对冲后'),
        'fig_turn': _plot_turn_hold(df_plot[['date', 'turnover', 'hold_num']]),

    })
