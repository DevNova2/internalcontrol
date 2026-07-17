# -*- coding: utf-8 -*-
"""
@author: Neo
@software: PyCharm
@file: vis_F_c.py
@time: 2023/5/20 18:31
说明:
"""
from math import pi
import numpy as np
import pandas as pd

import hvplot
import hvplot.pandas  # noqa

import holoviews as hv
from holoviews.util.transform import dim
from holoviews.selection import link_selections
from holoviews.operation import gridmatrix
from holoviews.operation.element import histogram
from holoviews import opts

from bokeh.palettes import Category20c
from bokeh.plotting import figure, save
from bokeh.transform import cumsum
from ShuiDQReport.settings import BASE_DIR
from Datas.load_data import LoadData

pd.options.plotting.backend = 'holoviews'
hv.extension('bokeh', 'plotly')


class F_C_View(object):
    def __init__(self,ld):
        self.inc_dir = str(BASE_DIR) + "/mult_factor/templates/mult_factor/F_C/"

        self.ld = ld
        self.df, self.cols = self.ld.get_factors_weights(F_all=True)

        self.ddf = None

    def html_weights(self):
        if self.ddf is None:
            self._get_ddf()
        self._weights_table()
        self._weights_scatter()
        self._weights_boxes()
        self._weights_3d()

    def _get_ddf(self):
        ddf = pd.DataFrame()
        for col in self.cols:
            df1 = self.df[col]
            dict_df1 = {'date': df1.index, 'value': df1.values, 'F_C': col}
            ddf = pd.concat([ddf, pd.DataFrame(dict_df1)])
        ddf.dropna(inplace=True)
        self.ddf = ddf

    def _weights_boxes(self):
        """因子池：各因子出现次数，因子权重分布"""
        boxplot = self.ddf.hvplot.box(y='value', by='F_C', height=self.ld.high, width=self.ld.width1,
                                      title="因子权重分布")
        t_plot = self.ddf["F_C"].value_counts().hvplot.bar(invert=True, flip_yaxis=True, height=self.ld.high,
                                                           title="各因子出现次数，总交易日：{}".format(self.df.shape[0]))
        layout = t_plot + boxplot
        layout.opts(
            shared_axes=False,
        )
        print(layout)

        hv.save(layout, self.inc_dir + "weights_boxes.html")

    def _weights_3d(self):
        """因子池3D权重分布"""
        hv.Store.set_current_backend('plotly')
        ds = hv.Dataset(self.ddf)
        scatter3d = hv.Scatter3D(ds, ['F_C', 'date', 'value'])
        scatter3d.opts(
            height=self.ld.high, width=self.ld.width1,
            title="因子池各因子权重分布"
        )
        print(scatter3d)
        hv.save(scatter3d, self.inc_dir + "weights_3d.html")

    def _weights_scatter(self):
        """因子池权重散点图"""
        overlay = hv.NdOverlay({group: hv.Scatter(([group] * self.df[group].dropna().count(),
                                                   self.df[group].dropna().values))
                                for i, group in enumerate(self.cols)})
        errorbars = hv.ErrorBars([(k, el.reduce(function=np.mean), el.reduce(function=np.std))
                                  for k, el in overlay.items()])

        html = errorbars * overlay
        html.opts(
            opts.ErrorBars(line_width=5, ),
            opts.Scatter(jitter=0.2, alpha=0.5, size=1, tools=['hover'], height=self.ld.high, width=self.ld.width1,
                         title="因子池权重散点图"),
        )
        print(html)
        hv.save(html, self.inc_dir + "weights_scatter.html")

    def _weights_table(self):
        # self.df['date'] = pd.to_datetime(self.df.index, format='%Y-%m-%d')
        des_table = self.df.describe().T.sort_values('count', ascending=False)
        des_table.reset_index(inplace=True, names="facotrs")
        html = des_table.hvplot.table()
        title = "因子池权重统计表，区间【{} - {}】".format(self.df.index.values[0], self.df.index.values[-1])
        html.opts(
            opts.Table(title=title)
        )
        print(html)
        hv.save(html, self.inc_dir + "weights_table.html")

    def html_ics_IR(self):
        df_ics, df_IR = self.ld.get_ics()

        htmap = df_ics.corr().hvplot.heatmap(
            x='columns', y='index',
            title='F_C 各子因子相关性分析',
            cmap=["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce", "#ddb7b1", "#cc7878", "#933b41", "#550b1d"],
            xaxis='top', rot=30, width=self.ld.width1, ).opts(
            toolbar=None, fontsize={'title': 15, 'xticks': 10, 'yticks': 10}
        )
        print(htmap)
        # hv.save(htmap, self.inc_dir + "inc_ics_heatmap.html")

        factors = list(self.ld.get_factors_weights()[1].keys())
        overlay = hv.NdOverlay({interp: hv.Curve(df_IR, 'date', interp).opts(tools=['hover']) for interp in factors})
        overlay.opts(legend_position='top', width=self.ld.width1, show_grid=True,
                     xlabel="日期（自2009年起）", ylabel="IR",
                     title="复合因子 F_C 各子因子IR走势")
        print(overlay)
        hv.save(htmap + overlay, self.inc_dir + "inc_ic_ir.html")


def html_weights_pie(height=350):
    """对当天得F_C 因子池及其权重用饼状图展示"""
    lda = LoadData()
    date, x = lda.get_factors_weights()

    data = pd.Series(x).reset_index(name='value').rename(columns={'index': 'F_c'})
    data['angle'] = data['value'] / data['value'].sum() * 2 * pi
    data['color'] = Category20c[len(x)]

    p = figure(height=height, title="复合因子F_C权重成分，日期：{}".format(date), toolbar_location=None,
               tools="hover", tooltips="@F_c: @value", x_range=(-0.5, 1.0))

    p.wedge(x=0, y=1, radius=0.4,
            start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
            line_color="white", fill_color='color', legend_field='F_c', source=data)

    p.axis.axis_label = None
    p.axis.visible = False
    p.grid.grid_line_color = None
    return p

    # save(p, "weights_pie.html", resources="cdn", title="F_C_weights")


if __name__ == '__main__':
    fc = F_C_View(ld=LoadData())
    fc.html_ics_IR()
    # 这个3D模块要放最后执行
    fc.html_weights()
