#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/9 15:47
# @Author  : Neo
# @File    : load_data.py
# @Software: PyCharm
# 说明:
import datetime
import numpy as np
import pandas as pd
from Utils.utils import trans_str_to_float64
from Datas.load_data import Load


class LoadData(Load):
    def __init__(self):
        super().__init__()

        self.today = datetime.date.today().isoformat()
        self.the_date = None
        self.the_yesterday = None

        self.df_cap = None

    def get_the_date(self):

        dates = list(self.client_u.economic.trade_dates.find({'trade_date': {'$lte': self.today}},
                                                             {"_id": 0, }).sort('trade_date', -1).limit(2))

        self.the_date, self.the_yesterday = dates[0]["trade_date"], dates[1]["trade_date"]

    def get_pre_cap_chg(self, date_s=None, date_e=None):
        if self.the_yesterday is None:
            self.get_the_date()
        if date_s is None or date_e is None:
            df1 = pd.DataFrame(self.client_u.basic_wind.w_basic_financial.find({'date': self.the_yesterday, },
                                                                               {"_id": 0, 'date': 1, "code": 1, "mkt_cap_ard": 1}))
            df2 = pd.DataFrame(self.client_u.basic_wind.w_vol_price.find({'date': self.the_yesterday, },
                                                                         {"_id": 0, 'date': 1, "code": 1, "pct_chg": 1}))
        else:
            df1 = pd.DataFrame(self.client_u.basic_wind.w_basic_financial.find({'date': {'$gte': date_s, '$lte': date_e}, },
                                                                               {"_id": 0, 'date': 1, "code": 1, "mkt_cap_ard": 1, }))
            df2 = pd.DataFrame(self.client_u.basic_wind.w_vol_price.find({'date': {'$gte': date_s, '$lte': date_e}, },
                                                                         {"_id": 0, 'date': 1, "code": 1, "pct_chg": 1}))
            if df1.empty and df2.empty:
                # 周一或者月初第一天
                return pd.DataFrame()

        df = pd.merge(df1, df2, on=['date', 'code'])
        df = trans_str_to_float64(df, trans_cols=['mkt_cap_ard', 'pct_chg'])
        return df

    def get_today_chg(self):
        if self.the_yesterday is None:
            self.get_the_date()
        df = pd.DataFrame(self.client_u.basic_jq.jq_daily_price_none.find({'date': {'$in': [self.the_yesterday, self.the_date]}, },
                                                                          {"_id": 0, 'date': 1, "code": 1, "close": 1}))
        df.sort_values('date', inplace=True)
        dfx = df.groupby('code').apply(lambda dx: dx.close.pct_change()).dropna().droplevel(level=1)
        dfx.name = 'pct_chg'
        dfx = dfx.reset_index()
        dfx.insert(0, 'date', self.the_date)

        return dfx


if __name__ == '__main__':
    xx = LoadData()
    xx.close()
