# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: load_data.py
@time: 2023/5/20 19:09
说明:
"""
import datetime
import numpy as np
import pandas as pd
import pymongo
from Datas.db_client import get_client

from Utils.utils import trans_str_to_float64, get_screen_size

pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.max_columns', None)
pd.set_option('expand_frame_repr', False)


class Load:
    def __init__(self):
        self.client_u = get_client(c_from='db_u')
        self.client_neo = get_client(c_from='neo')

        self.today = datetime.date.today().isoformat()

        screen_size = get_screen_size()
        self.width1 = int(screen_size[0] * 1 / 3)
        self.width_h = int(screen_size[0] / 2)
        self.width2 = int(screen_size[0] * 2 / 3)
        self.width25 = int(screen_size[0] * 2 / 5)
        self.width3 = int(screen_size[0] * 0.95)
        self.high = self.width1
        self.high2 = int(self.high / 2)

    def close(self):
        self.client_u.close()
        self.client_neo.close()


class LoadData(object):
    def __init__(self):
        client = pymongo.MongoClient(CLIENT)
        self.db_stat = client[DATABASE_STAT]
        self.db_trade = client[DB_TRADE_DETAIL]
        self.db_stra = client[DATABASE_STRATEGY]
        self.db_basic = client[DATABASE_BASIC]
        self.db_bt = client[DATABASE_BACKTEST]

        self.the_date = None
        self.the_last_date = None
        self.df_industries = None
        self.df_cap = None

        screen_size = get_screen_size()
        self.width1 = int(screen_size[0] * 1 / 3)
        self.width_h = int(screen_size[0] / 2)
        self.width2 = int(screen_size[0] * 2 / 3)
        self.width25 = int(screen_size[0] * 2 / 5)
        self.width3 = int(screen_size[0] * 0.95)
        self.high = self.width1
        self.high2 = int(self.high / 2)

        self.tmp_dates_chg_df = None

    def get_the_date(self):
        dates = list(self.db_stra['factor_weights'].find({}, {"_id": 0, "date": 1}).sort('date', -1).limit(2))
        the_date = dates[0]["date"]
        the_last_date = dates[1]["date"]
        self.the_date = the_date
        self.the_last_date = the_last_date
        return the_date

    def get_industries(self, the_day=None):
        if the_day is None:
            raise Exception("指定日期不能为空呀！！")
        df_ind = pd.DataFrame(self.db_basic['jq_daily_industries'].find(
            {'date': the_day, }, {"_id": 0, "name": 1, "stocks": 1}))
        self.df_industries = df_ind
        return df_ind

    def get_cap_and_log(self, the_day=None):
        if the_day is None:
            raise Exception("指定日期不能为空呀！！")
        df_cap = pd.DataFrame(self.db_basic['w_stocks_daily'].find(
            {'date': the_day, }, {"_id": 0, "code": 1, "market_cap": 1}))
        df_cap['log_market_cap'] = np.log(df_cap['market_cap'])
        df_cap["market_cap"] = (df_cap.market_cap / 100000000).round(1)
        self.df_cap = df_cap
        return df_cap

    def get_trade_loss(self):
        df_loss = pd.DataFrame(self.db_stat['trade_loss_2307'].find({}, {"_id": 0, }))
        df_loss.sort_values('date', inplace=True)
        return df_loss

    def __filter_blacklist(self, df_from, the_day=None):
        if the_day is None:
            raise Exception("指定日期不能为空呀！！")
        df = df_from.copy()
        df_black = pd.DataFrame(self.db_stra['blacklist'].find({'date': the_day}, {"_id": 0, }))
        filtered = df[~df.code.isin(df_black.code.values)]
        return filtered

    def __get_the_factor(self, factor=None, the_day=None, date_s='2022-01-01', date_e='2022-12-31'):
        if factor is None:
            raise Exception("没有指定factor，怎么搞？")
        if the_day is None:
            qds = {"date": {'$gte': date_s, '$lte': date_e}}
        else:
            qds = {'date': the_day}
        if factor == "mv_vol":
            df = pd.DataFrame(self.db_stra['factors_market_rank_snd'].find(
                qds, {"_id": 0, "date": 1, "code": 1, "mv_vol": 1}, batch_size=1000000))
            df = trans_str_to_float64(df, trans_cols=['mv_vol'])
            # 这个因子反向用的
            df.sort_values('mv_vol', ascending=True, inplace=True)
        elif factor == "F_C":
            df = pd.DataFrame(self.db_stra['stocks_FC'].find(qds, {"_id": 0, }, batch_size=1000000).sort('F_c', -1))
            df = trans_str_to_float64(df, trans_cols=['F_c'])
        elif factor == "F1":
            df = pd.DataFrame(self.db_stra['stocks_all'].find(qds, {"_id": 0, }, batch_size=1000000).sort('F1', -1))
            df = trans_str_to_float64(df, trans_cols=['F1'])
        elif factor in ["F_EBIT2P", "F_EPS", "F_NIGttm", "F_ret_com", "F_SalesGttm", "F_cfo2roi", ]:
            df = pd.DataFrame(self.db_stra['factors_apt_and_rank'].find(
                qds, {"_id": 0, "date": 1, "code": 1, factor: 1}, batch_size=1000000))
            df = trans_str_to_float64(df, exp_cols=['date', 'code'])
            # if factor == "F_ret_com":  # 这个因子反向用的
            #     df.sort_values(factor, ascending=True, inplace=True)
            # else:
            #     df.sort_values(factor, ascending=False, inplace=True)
        else:
            raise Exception("指定的因子-->>{}有问题呀".format(factor))
        return df

    def get_chg_factor(self, factor=None):
        """单因子 对应第二天的涨跌幅数据"""
        if factor is None:
            raise Exception("没有指定factor，怎么搞？")
        if self.the_date is None:
            self.get_the_date()
        df_cha = pd.DataFrame(self.db_basic['w_stocks_chg'].find({'date': self.the_date}, {"_id": 0, }))
        df_cha = trans_str_to_float64(df_cha, trans_cols=['chg', ])
        df_factor = self.__get_the_factor(factor=factor, the_day=self.the_last_date)
        df_factor = self.__filter_blacklist(df_factor, the_day=self.the_last_date)
        df = pd.merge(df_factor, df_cha, on="code")
        return df

    def get_about_factor(self, factor=None):
        """单因子 行业、市值"""
        if factor is None:
            raise Exception("没有指定factor，怎么搞？")
        if self.the_date is None:
            self.get_the_date()
        df_factor = self.__get_the_factor(factor=factor, the_day=self.the_date)
        df_factor = self.__filter_blacklist(df_factor, the_day=self.the_date)

        if self.df_industries is None:
            self.get_industries(the_day=self.the_date)
        for row in self.df_industries.itertuples(index=False):
            stocks = eval(getattr(row, "stocks"))
            if len(stocks) > 0:
                ind_name = str(getattr(row, "name"))
                stocks = list(map(lambda x: 'SH' + x[:6] if x.startswith('6') else 'SZ' + x[:6], stocks))
                df_factor.loc[df_factor.code.isin(stocks), 'ind'] = ind_name
        if not df_factor[df_factor.ind.isna()].empty:
            raise Exception("居然没匹配到行业？？？？")
        if self.df_cap is None:
            self.get_cap_and_log(the_day=self.the_date)
        df = pd.merge(df_factor, self.df_cap, on="code")

        return df

    def get_factors_weights(self, F_all=False):
        if F_all:
            df = pd.DataFrame(self.db_stra['factor_weights'].find({}, {"_id": 0, }))
            df.set_index('date', inplace=True)
            cols = [col for col in list(df) if col.startswith("F_")]
            df = trans_str_to_float64(df, trans_cols=cols)
            df = df[cols]
            return df, cols
        else:
            df = pd.DataFrame(self.db_stra['factor_weights'].find({}, {"_id": 0, }).sort('date', -1).limit(1))
            df.set_index('date', inplace=True)
            cols = eval(df.iloc[-1]['factors'])
            df = trans_str_to_float64(df, trans_cols=cols)
            df = df[cols]
            return df.index.values[0], df.iloc[-1].to_dict()

    def get_ics(self, the_factors=True):
        if the_factors:
            factors = dict.fromkeys(self.get_factors_weights()[1], 1)
            factors.update({"_id": 0, "date": 1})
            df_ics = pd.DataFrame(self.db_stra['factor_IC'].find({}, factors))
        else:
            df_ics = pd.DataFrame(self.db_stra['factor_IC'].find({}, {"_id": 0, }))
        df_ics = trans_str_to_float64(df_ics, exp_cols=['date', ])
        df_ics.set_index('date', inplace=True)
        df_ics.sort_index(inplace=True)
        df_IR = pd.DataFrame()
        dates = df_ics[df_ics.index > '2009-01-01'].index.unique().tolist()
        for date in dates:
            data_ics = df_ics.loc[:date]
            IRs = np.sqrt(250) * (data_ics.mean() / data_ics.std())
            dff = abs(pd.DataFrame(IRs).T)
            dff.insert(0, 'date', date)
            df_IR = pd.concat([df_IR, dff])
        df_IR['date'] = pd.to_datetime(df_IR.date)
        return df_ics, df_IR


    def get_alpha_one(self):
        """实盘@1"""
        df = pd.DataFrame(self.db_stat['dq_alpha_one'].find(
            {}, {"_id": 0, "净值日期": 1, "累计净值  (元)": 1, "资产净值  (元)": 1, "实收资本  (元)": 1, }))
        df['净值日期'] = pd.to_datetime(df['净值日期'])
        df.sort_values('净值日期', inplace=True)
        df['chg'] = df['累计净值  (元)'].pct_change()
        df.dropna(inplace=True)
        df['year'] = df['净值日期'].dt.year
        return df

    def get_dates_bench_chg(self, date_s='2022-01-01', date_e='2022-12-31'):
        """拉取基准收益率，为可视化超额展示提供数据"""
        df = pd.DataFrame(self.db_basic['w_bench_close'].find(
            {"date": {'$gte': date_s, '$lte': date_e}}, {"_id": 0, }, batch_size=1000000))

        df['沪深300'] = df['000300.SH'] / df.iloc[0]["000300.SH"] - 1
        df['中证500'] = df['000905.SH'] / df.iloc[0]["000905.SH"] - 1

        df_res = df[['date', '沪深300', '中证500']].copy()
        return df_res

    def get_dates_chg(self, date_s='2022-01-01', date_e='2022-12-31'):
        """拉取指定日期范围类的全A股票涨跌幅数据"""
        df_chg = pd.DataFrame(self.db_basic['w_stocks_chg'].find(
            {"date": {'$gte': date_s, '$lte': date_e}}, {"_id": 0, }, batch_size=1000000))
        df_chg = trans_str_to_float64(df_chg, trans_cols=['chg', ])
        df_chg.set_index(['date', 'code'], inplace=True)
        df_chg.sort_index(inplace=True)
        self.tmp_dates_chg_df = df_chg
        return df_chg

    def get_layer_factor(self, factor=None, date_s='2022-01-01', date_e='2022-12-31'):
        """分层回测单调性"""
        df_factor = self.__get_the_factor(factor, date_s=date_s, date_e=date_e)
        df_factor.set_index(['date', 'code'], inplace=True)
        df_factor.sort_index(inplace=True)
        return df_factor
