from django.shortcuts import render

#from django.shortcuts import render
#from dash import Dash, dcc, html
#from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import datetime
import json
from pathlib import Path
#import os

# 获取当前日期
today = datetime.date.today().isoformat()
#today = '2024-07-30'  # 可用于测试

# 文件路径
file_path1 = rf'\\DESKTOP-240I8GD\Users\a\Desktop\xtquant\asset\realtime\{today}-gy.csv'
file_path2 = rf'\\DESKTOP-240I8GD\Users\a\Desktop\xtquant\asset\realtime\{today}-df.csv'
trade_file = rf'\\DESKTOP-240I8GD\Users\a\Desktop\xtquant\asset\turnover.json'

def _load_trade_payload():
    try:
        with open(trade_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        today_data = data.get(today, {})
        return today_data.get('sell', {}), today_data.get('buy', {})
    except FileNotFoundError:
        return {}, {}


def _safe_chart(chart_fn, *args):
    try:
        return chart_fn(*args)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return go.Figure().to_html(full_html=False, include_plotlyjs=True)


# 初始化Dash应用

#app = Dash(__name__, server=False)
'''
app.layout = html.Div([
    html.Div([
        dcc.Graph(id='live-update-graph1', style={'display': 'inline-block', 'width': '49%'}),
        dcc.Graph(id='live-update-graph3', style={'display': 'inline-block', 'width': '49%'})
    ]),
    html.Div([
        dcc.Graph(id='live-update-graph2', style={'display': 'inline-block', 'width': '49%'}),
        dcc.Graph(id='live-update-graph4', style={'display': 'inline-block', 'width': '49%'})
    ]),
    dcc.Interval(
        id='interval-component',
        interval=1*60000,  # 更新间隔，单位为毫秒，这里是60秒
        n_intervals=0
    )
])
'''
'''
app.layout = html.Div([
    html.Div([
        dcc.Graph(id='live-update-graph1', style={'display': 'inline-block', 'width': '100%', 'height': '50vh'}),
        dcc.Graph(id='live-update-graph3', style={'display': 'inline-block', 'width': '100%', 'height': '50vh'})
    ], style={'display': 'flex', 'flex-direction': 'column', 'width': '49%', 'height': '100vh'}),
    html.Div([
        dcc.Graph(id='live-update-graph2', style={'display': 'inline-block', 'width': '100%', 'height': '50vh'}),
        dcc.Graph(id='live-update-graph4', style={'display': 'inline-block', 'width': '100%', 'height': '50vh'})
    ], style={'display': 'flex', 'flex-direction': 'column', 'width': '49%', 'height': '100vh'}),
    dcc.Interval(
        id='interval-component',
        interval=1*60000,  # 更新间隔，单位为毫秒，这里是60秒
        n_intervals=0
    )
], style={'display': 'flex', 'width': '100%', 'height': '100vh'})

'''
'''
app.layout = html.Div([
    html.Div([
        dcc.Graph(id='live-update-graph1', style={'width': '100%', 'height': '50vh'}),
        dcc.Graph(id='live-update-graph2', style={'width': '100%', 'height': '50vh'})
    ], style={'width': '49%', 'display': 'inline-block'}),
    html.Div([
        dcc.Graph(id='live-update-graph3', style={'width': '100%', 'height': '50vh'}),
        dcc.Graph(id='live-update-graph4', style={'width': '100%', 'height': '50vh'})
    ], style={'width': '49%', 'display': 'inline-block'}),
    dcc.Interval(
        id='interval-component',
        interval=1*60000,  # 更新间隔，单位为毫秒，这里是60秒
        n_intervals=0
    )
], style={'display': 'flex'})
'''
def create_individual_figure(file, buy, sell, title):
    df = pd.read_csv(file, index_col=0)
    df.index = [i[:-3] for i in df.index]

    fig = make_subplots(specs=[[{"secondary_y": False}]])

    for stk in buy.get(title, []):
        stk = stk[2:] + '.' + stk[:2]
        if stk in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[stk], mode='lines', name=stk, line=dict(color='red')))

    for stk in sell.get(title, []):
        stk = stk[2:] + '.' + stk[:2]
        if stk in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[stk], mode='lines', name=stk, line=dict(color='blue')))

    fig.update_yaxes(title_text="Individual Stock Value")
    fig.update_xaxes(tickangle=90)

    fig.update_layout(height=600,# width=1200,
                      title_text=f"换仓数据\t{title}", showlegend=False)

    return  fig.to_html(full_html=False, include_plotlyjs=True)

def create_total_figure(file):
    df = pd.read_csv(file, index_col=0)
    for index, row in df.iterrows():
        df.loc[index, 'total'] = row.sum()
    df.index = [i[:-3] for i in df.index]

    fig = make_subplots(specs=[[{"secondary_y": False}]])

    fig.add_trace(go.Scatter(x=df.index, y=df['total'], mode='lines', name='total', line=dict(
        color='black'), fill='tonexty', fillcolor='rgba(0,0,0,0.3)'))
    if df.index[-1] < '09:40':
        fig.update_yaxes(title_text="Total Value")
        fig.update_xaxes(tickangle=90)

        fig.update_layout(height=600, #width=1200,
                          title_text=f"总市值\t{file[-6:-4]}", showlegend=True)

        return fig.to_html(full_html=False, include_plotlyjs=True)


    df_after_930 = df.loc[df.index >= '09:31']
    max_total = df_after_930['total'].max()
    min_total = df_after_930['total'].min()
    delta = max_total - min_total

    fig.update_yaxes(title_text="Total Value", range=[
                     min_total-3/3*delta, max_total+3/3*delta])
    fig.update_xaxes(tickangle=90)

    fig.update_layout(height=600, #width=1200,
                      title_text=f"总市值\t{file[-6:-4]}", showlegend=True)

    return fig.to_html(full_html=False, include_plotlyjs=True)
    
'''
@app.callback(
    [Output('live-update-graph1', 'figure'),
     Output('live-update-graph2', 'figure'),
     Output('live-update-graph3', 'figure'),
     Output('live-update-graph4', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
'''
def dash_app_view(request):
    sell, buy = _load_trade_payload()

    context = {
        'trade_date': today,
        'fig1': _safe_chart(create_individual_figure, file_path1, buy, sell, file_path1[-6:-4]),
        'fig2': _safe_chart(create_individual_figure, file_path2, buy, sell, file_path2[-6:-4]),
        'fig3': _safe_chart(create_total_figure, file_path1),
        'fig4': _safe_chart(create_total_figure, file_path2),
        
    }
    return render(request, 'stocks_trade/dash_app.html', context)

    '''
    fig1 = create_individual_figure(file_path1, buy, sell, file_path1[-6:-4])
    fig2 = create_individual_figure(file_path2, buy, sell, file_path2[-6:-4])
    fig3 = create_total_figure(file_path1)
    fig4 = create_total_figure(file_path2)
    return fig1, fig2, fig3, fig4
    '''




