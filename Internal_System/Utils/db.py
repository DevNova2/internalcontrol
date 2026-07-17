# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: db.py
@time: 2023-07-27 16:42
说明:
"""
import json
import psutil
from concurrent.futures import ThreadPoolExecutor
import pymongo
from pymongo import InsertOne
import pandas as pd
import numpy as np
from loguru import logger


def _thread_insert2db(table: pymongo.collection = None, df: pd.DataFrame = None) -> None:
    df.reset_index(inplace=True, drop=True)  # 丢弃DF索引后插入数据库
    data = list(json.loads(df.transpose().to_json()).values())
    try:
        table.insert_many(data, ordered=False)
    except Exception as e:
        logger.warning(f'{str(e)[:300]}')
        requests = list(map(lambda d: InsertOne(d), data))
        result = table.bulk_write(requests, ordered=False)
        logger.info(f'异常情况下写入了 -->> {result.inserted_count} 条，PS:总共（{len(data)}）条')


def insert_db_from_df(table: pymongo.collection = None, df: pd.DataFrame = None) -> None:
    if table is None or df is None:
        raise Exception("必须传入数据表，数据(df格式)")
    if df.empty:
        raise Exception("数据 df 为空，请检查！目标table：{}".format(table))
    df_len = df.shape[0]
    if df_len > 1500000:
        cpus = int(psutil.cpu_count(logical=False) * 0.7)
        logger.info(f'数据量为：{df_len}，将分拆成 {cpus} 个线程 分布入库')
        df_list = np.array_split(df, cpus)
        arg_list = [(table, df_) for df_ in df_list]
        with ThreadPoolExecutor(max_workers=cpus) as pool:
            pool.map(lambda arg: _thread_insert2db(*arg), arg_list)
    else:
        _thread_insert2db(table=table, df=df)


def df_trans_to_str_and_insert_db(table: pymongo.collection = None, df: pd.DataFrame = None) -> None:
    df_str = df.astype(str)
    insert_db_from_df(table, df_str)
