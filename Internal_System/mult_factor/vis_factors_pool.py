# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: vis_factors_pool.py
@time: 2023/5/28 13:03
说明:
"""
import numpy as np
import pandas as pd
import hvplot
import hvplot.pandas  # noqa

import holoviews as hv
from holoviews.util.transform import dim
from holoviews import opts

from ShuiDQReport.settings import BASE_DIR
from Datas.load_data import LoadData

pd.options.plotting.backend = 'holoviews'
hv.extension('bokeh', )


class FactorsPoolView(object):

    def __init__(self,ld):
        self.inc_dir = str(BASE_DIR) + "/mult_factor/templates/mult_factor/factors_pool/"

        self.ld = ld
        self.df_ics, self.df_IR = self.ld.get_ics(the_factors=False)
        self.alpha_factors = {
            'value': ['F_B2P', 'F_E2P', 'F_S2P', 'F_EBIT2P', 'F_cfo2ev', ],
            'quality': ['F_ROE', 'F_ROA', 'F_EPS', 'F_LOAR', 'F_NI2S', 'F_GPM', 'F_C2E', 'F_cfo2roi', ],
            'growth': ['F_ebitGttm', 'F_NIGttm', 'F_SalesGttm', ],
            'momentum': ['F_ret_com', ],
        }

    def html_corr(self):
        df_ics = self.df_ics.copy()
        htmap_all = df_ics.corr().hvplot.heatmap(
            x='columns', y='index', title='因子池因子相关性分析',
            cmap=["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce", "#ddb7b1", "#cc7878", "#933b41", "#550b1d"],
            xaxis='top', rot=45, width=self.ld.width1, height=self.ld.high).opts(
            toolbar=None, fontsize={'title': 15, 'xticks': 10, 'yticks': 10}
        )
        print(htmap_all)
        hv.save(htmap_all, self.inc_dir + "inc_corr_all.html")

        category = list(self.alpha_factors.keys())[:3]
        lay = hv.Overlay()
        for cat in category:
            htmap = df_ics[self.alpha_factors[cat]].corr().hvplot.heatmap(
                x='columns', y='index', title='分类展示相关性',
                cmap=["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce", "#ddb7b1", "#cc7878", "#933b41",
                      "#550b1d"],
                xaxis='top', rot=45, width=self.ld.width1, height=self.ld.high).opts(
                toolbar=None, fontsize={'title': 15, 'xticks': 10, 'yticks': 10}
            )
            lay = lay * htmap
        print(lay)
        hv.save(lay, self.inc_dir + "inc_corr_sub.html")
        layout = htmap_all + lay
        layout.opts(shared_axes=False).cols(2)
        hv.save(layout, self.inc_dir + "inc_corr.html")

    def html_ics(self):
        df_ics = self.df_ics.copy()
        df_ics = abs(df_ics)

        box_all = df_ics.plot.box(invert=True, width=self.ld.width2, height=self.ld.high, title="全类因子IC值分布")

        hv.save(box_all, self.inc_dir + "inc_ics_all_box.html")

        lay = hv.Layout()
        for k, v in self.alpha_factors.items():
            box = df_ics[v].plot.box(width=self.ld.width1, shared_axes=False, title=k)
            lay = lay + box
        lay.opts(title="分类因子IC分布").cols(2)
        print(lay)
        hv.save(lay, self.inc_dir + "inc_ics_sub.html")

    def html_irs(self):
        df_IR = self.df_IR.copy()
        cols = df_IR.columns.values.tolist()
        cols.remove('date')

        overlay = hv.NdOverlay({col: hv.Curve(df_IR, 'date', col).opts(tools=['hover']) for col in cols})
        overlay.opts(legend_position='top', width=self.ld.width2, height=self.ld.high,
                     show_grid=True, xlabel="日期（自2009年起）", ylabel="IRS", title="全类因子IR走势曲线")
        print(overlay)
        hv.save(overlay, self.inc_dir + "inc_irs_all.html")

        lay = hv.Layout()
        for k, v in self.alpha_factors.items():
            overlay = hv.NdOverlay(
                {col: hv.Curve(df_IR, 'date', col).opts(tools=['hover']) for col in v})
            overlay.opts(legend_position='top', width=self.ld.width1, height=self.ld.high, shared_axes=False,
                         show_grid=True, xlabel="日期（自2009年起）", ylabel="IRS", title=k)
            lay = lay + overlay
        lay.opts(title="分类因子IR走势", shared_axes=False).cols(2)
        print(lay)
        hv.save(lay, self.inc_dir + "inc_irs_sub.html")


if __name__ == '__main__':
    fp = FactorsPoolView(ld=LoadData())
    fp.html_corr()
    fp.html_ics()
    fp.html_irs()
