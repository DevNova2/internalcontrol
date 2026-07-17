#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/11 19:32
# @Author  : Neo
# @File    : load_data.py
# @Software: PyCharm
# 说明:

import pandas as pd
from Datas.load_data import Load


class LoadData(Load):
    def __init__(self):
        super().__init__()

    def get_pt_chg(self, stra_name="alpha_first"):
        dict_stra = {"alpha_first": "chg_alpha_first_v2_0", 'yk_first': 'chg_yk_first_v2_0'}
        table_name = dict_stra.get(stra_name)
        if table_name is None:
            raise Exception("传入的统计表 {} 名称有误，请检查==>>{}".format(stra_name, dict_stra))
        df = pd.DataFrame(self.client_neo['bt_paper_trade'][table_name].find({}, {"_id": 0, }))

        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)
        df['loss'] = 0.0053
        df.loc['2023-09-01':, 'loss'] = 0.0048
        df['chg4_'] = df.chg - df.turnover * df.loss

        df['net_value'] = (df.chg + 1).cumprod()
        df['net_value4_'] = (df.chg4_ + 1).cumprod()

        return df.drop(columns=['loss'])


if __name__ == '__main__':
    pass
