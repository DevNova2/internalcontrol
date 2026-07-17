#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/5 16:15
# @Author  : Neo
# @File    : data.py
# @Software: PyCharm
# 说明:
import sys
sys.path.append("D:\company_project\ShuiDQReport")
from loguru import logger
import pandas as pd
from Datas.db_client import get_client
from Utils.db import insert_db_from_df

pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('expand_frame_repr', False)
pd.set_option('display.max_columns', None)
pd.set_option('display.precision', 14)


class LoadCsv2DB:
    """产品净值入库"""

    def __init__(self):
        self.csv_dir = 'D:/company_project/产品净值/'

        self.db = get_client(c_from='neo')['product']

        self.ID_ALPHA_FIRST = 'SEY112'
        self.ID_YK_FIRST = 'SB5663'

    def _csv2db(self, df: pd.DataFrame, pro_id: str, build_index: bool = False):
        if pro_id == self.ID_ALPHA_FIRST:
            t = self.db['net_value_alpha_first']
        elif pro_id == self.ID_YK_FIRST:
            t = self.db['net_value_yk_first']
        else:
            raise Exception(f'指定产品名有误！！！')
        if build_index:
            t.create_index([("date", 1), ], background=True, unique=True)
        date = next(t.find({}, {'_id': 0, 'date': 1}).sort([('date', -1)])).get('date')
        ddf = df.loc[df.date > date]
        if all(pd.Index(['date', '单位净值', '累计净值', '资产净值', '实收资本'], dtype='object') == ddf.columns):
            insert_db_from_df(t, df=ddf)
            logger.info(f'入库完成！')
        else:
            raise Exception(f'导入格式不对，请检查！！')

    def alpha_first2db(self, csv_name: str):
        logger.info(f'开始导入产品净值：阿尔法1号！')
        df = pd.read_excel(self.csv_dir + csv_name, engine='openpyxl')
        if not df['产品代码'].iloc[-1] == self.ID_ALPHA_FIRST:
            raise Exception(f'不是阿尔法1号，请检查！！')
        ds = df.rename(
            columns={'净值日期': 'date', '单位净值  (元)': '单位净值', '累计净值  (元)': '累计净值', '资产净值  (元)': '资产净值',
                     '实收资本  (元)': '实收资本'}).drop(columns=['产品代码', '产品名称'])
        self._csv2db(ds, pro_id=self.ID_ALPHA_FIRST, build_index=False)

    def yk_first2db(self, csv_name: str):
        logger.info(f'开始导入产品净值：屿阔1号！')
        df = pd.read_excel(self.csv_dir + csv_name, engine='openpyxl')
        if not df['产品代码'].iloc[-1] == self.ID_YK_FIRST:
            raise Exception(f'不是屿阔1号，请检查！！')
        ds = df.rename(
            columns={'净值日期': 'date', '基金资产净值': '资产净值', '实收资本  (元)': '实收资本'}).drop(
            columns=['产品代码', '产品名称'])
        ds['资产净值'] = ds['资产净值'].map(lambda x: x.replace(',', '')).astype(float)
        # ds['实收资本'] = ds['实收资本'].map(lambda x: x.replace(',', '')).astype(float)
        self._csv2db(ds, pro_id=self.ID_YK_FIRST, build_index=False)


if __name__ == '__main__':
    xx = LoadCsv2DB()
    xx.alpha_first2db('净值表excel版 (13).xlsx')
    #xx.yk_first2db('202401-屿阔.xlsx')
