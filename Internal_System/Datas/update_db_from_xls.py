# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: load_data.py
@time: 2023/5/22 17:19
说明:
"""
import sys
sys.path.append("D:\company_project\ShuiDQReport")
import ctypes
import difflib
import numpy as np
import pandas as pd
import pymongo
from pymongo import IndexModel
from Utils.db import insert_db_from_df
#from ShuiDQReport.settings import CLIENT, DATABASE_STAT, DATABASE_BASIC, DATABASE_STRATEGY
from Utils.utils import trans_str_to_float64

pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
# 显示所有列
pd.set_option('display.max_columns', None)
# True就是可以换行显示。设置成False的时候不允许换行
pd.set_option('expand_frame_repr', False)


class InsertDb:
    def __init__(self):
        self.csv_dir = 'D://company_project/'
        client = pymongo.MongoClient("mongodb://192.168.1.77:27017/")
        self.db_stat = client['product']

    def close(self):
        self.db_stat.client.close()

    def insert_db(self, csv_name='./净值表excel版 (7).xlsx', update=True):
        csv_file = self.csv_dir + csv_name
        df_csv = pd.read_excel(csv_file, engine="openpyxl", header=0)
        # print(df_csv)

        table = self.db_stat['dq_alpha_one']
        if update:
            date = list(table.find({}, {"_id": 0, "净值日期": 1}).sort('净值日期', -1).limit(1))[0]['净值日期']
            print("上次更新日期：{}".format(date))
            df_csv = df_csv[df_csv['净值日期'] > date].copy()
            df_csv.dropna(inplace=True)
            if df_csv.empty:
                print("没有最新数据，不做更新")
                return
            print(df_csv)
        else:
            table.create_index([("净值日期", pymongo.DESCENDING)], background=True, unique=True)
        # print(df_csv)
        insert_db_from_df(table=table, df=df_csv)


def update_db():
    inst = InsertDb()
    inst.insert_db(csv_name='净值表excel版 (7).xlsx')
    inst.close()


if __name__ == '__main__':
    update_db()
