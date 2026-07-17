import pandas as pd
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import datetime
import json
import os
import pymongo

def get_today_files():
    today = datetime.date.today().isoformat()
    url = 'mongodb://Neo:neox@192.168.1.99:29900/'
    file_path = rf"/mnt/trade_data/data/进取1-中信-股衍/{today}-gy.csv"
    trade_file = rf"/mnt/trade_data/turnover/{today}.json"
    order_file = rf"/mnt/trade_data/order/进取1-中信-股衍/{today.replace('-', '')}-order.csv"
    chg_file = rf"/mnt/trade_data/data/进取1-中信-股衍/chg/{today}.csv"
    curr_path = rf'/mnt/trade_data/data/进取1-中信-股衍/{today}'
    return today, url, file_path, trade_file, order_file, chg_file, curr_path


def get_mongo_last_day(today, url):
    try:
        date_client = pymongo.MongoClient(url)
        last_day = list(date_client['economic']['trade_dates'].find(
            {'trade_date': {'$lt': today}}).sort('trade_date', pymongo.DESCENDING))[0]['trade_date']
    except Exception as e:
        print(f"MongoDB连接失败: {e}")
        last_day = None
    return last_day

def get_trade_data(trade_file):
    try:
        with open(trade_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        sell = data.get('sell', {})
        buy = data.get('buy', {})
    except Exception as e:
        print(f"读取trade_file失败: {e}")
        sell, buy = {}, {}
    return sell, buy

def get_stock_options(file_path):
    try:
        df = pd.read_csv(file_path, index_col=0)
        stock_options = [{'label': col, 'value': col} for col in df.columns]
    except Exception as e:
        print(f"读取file_path失败: {e}")
        df = pd.DataFrame()
        stock_options = []
    return df, stock_options

def get_times(curr_path):
    try:
        names = os.listdir(curr_path)
        names.sort(reverse=True)
        times = [name[:6] for name in names if 'short' not in name]
    except Exception as e:
        print(f"读取curr_path失败: {e}")
        names, times = [], []
    return names, times

app = Dash(__name__)

# 初始化时动态获取
today, url, file_path, trade_file, order_file, chg_file, curr_path = get_today_files()
last_day = get_mongo_last_day(today, url)
sell, buy = get_trade_data(trade_file)
df, stock_options = get_stock_options(file_path)
names, times = get_times(curr_path)
curr_time = times[0] if times else '093100'
start_time = curr_time
if curr_time >= '133100' and len(times) > 1:
    start_time = [time for time in times if time > '093100'][-1]

def target_data_process(curr_time, start_time, curr_path):
    trade_file = curr_path+'/'+curr_time+'-gy-trade.csv'
    data_file = curr_path+'/'+curr_time+'-gy-data.csv'
    start_trade_file = curr_path+'/'+start_time+'-gy-trade.csv'
    # start_data_path = curr_path+'/'+start_time+'-gy-data.csv'  # 未使用，可保留路径如后续需要

    try:
        trade_df = pd.read_csv(trade_file, header=0)
        data_df = pd.read_csv(data_file, header=0)
        start_trade_df = pd.read_csv(start_trade_file, header=0)
        # 不再读取/覆盖 start_data_file，避免混淆
    except Exception as e:
        print(f"读取交易数据失败: {e}")
        return pd.DataFrame(), 0.0, 0.0
    
    trade_df = trade_df[trade_df['type'] != 'no_trade']
    
    buy_df = trade_df[(trade_df['type'] == 'turn') & (trade_df['direction'] == 1)]
    sell_df = trade_df[(trade_df['type'] == 'turn') & (trade_df['direction'] == -1)]

    if sell_df['start_amount'].sum() == 0:
        sell_process = 0.0
    else:
        sell_process = sell_df['amount'].sum() / sell_df['start_amount'].sum()
    
    if buy_df['target_amount'].sum() == 0:
        buy_process = 0.0
    else:
        buy_process = buy_df['amount'].sum() / buy_df['target_amount'].sum()

    # buy_process = 0.0
    # sell_process = 0.0

    if curr_time >= '133100':
        # 代码，当前数量，当前市值，2倍目标数量，开盘目标数量
        target_df = pd.DataFrame(
            columns=['代码', '当前数量', '当前市值', '2倍目标数量', '开盘目标数量'])

        target_df['代码'] = trade_df['code']

        for index, row in target_df.iterrows():
            code = row['代码']

            curr_amount = trade_df.loc[trade_df['code']
                                       == code, 'amount'].values[0]
            curr_value = curr_amount * \
                data_df.loc[data_df['code'] == code, 'lastPrice'].values[0]

            curr_target_amount = trade_df.loc[trade_df['code']
                                              == code, 'target_amount'].values[0]
            start_target_amount = start_trade_df.loc[start_trade_df['code']
                                                     == code, 'target_amount'].values[0]

            target_df.loc[index, '当前数量'] = curr_amount
            target_df.loc[index, '当前市值'] = curr_value

            if curr_target_amount == 0 and curr_amount == 0:
                target_df.loc[index, '2倍目标数量'] = '0.00%'
            elif curr_target_amount == 0:
                target_df.loc[index,
                              '2倍目标数量'] = '还没卖完'
            else:
                target_df.loc[index,
                              '2倍目标数量'] = curr_amount/curr_target_amount-1

            if start_target_amount == 0 and curr_amount == 0:
                target_df.loc[index, '开盘目标数量'] = 0

            elif start_target_amount == 0:
                target_df.loc[index,
                              '开盘目标数量'] = '还没卖完'
            else:
                target_df.loc[index,
                              '开盘目标数量'] = curr_amount/start_target_amount-1
    else:
        target_df = pd.DataFrame(
            columns=['代码', '当前数量', '当前市值', '开盘目标数量'])

        target_df['代码'] = trade_df['code']

        for index, row in target_df.iterrows():
            code = row['代码']

            curr_amount = trade_df.loc[trade_df['code']
                                       == code, 'amount'].values[0]
            curr_value = curr_amount * \
                data_df.loc[data_df['code'] == code, 'lastPrice'].values[0]

            curr_target_amount = trade_df.loc[trade_df['code']
                                              == code, 'target_amount'].values[0]

            target_df.loc[index, '当前数量'] = curr_amount
            target_df.loc[index, '当前市值'] = curr_value

            if curr_target_amount == 0 and curr_amount == 0:
                target_df.loc[index, '2倍目标数量'] = 0
                target_df.loc[index, '开盘目标数量'] = 0

            elif curr_target_amount == 0:
                target_df.loc[index,
                              '开盘目标数量'] = '还没卖完'
                target_df.loc[index,
                              '2倍目标数量'] = '还没卖完'
            else:
                target_df.loc[index,
                              '开盘目标数量'] = curr_amount/curr_target_amount-1
                target_df.loc[index,
                              '2倍目标数量'] = curr_amount/curr_target_amount-1

 
    return target_df, buy_process, 1 - sell_process

target_df, buy_process, sell_process = target_data_process(curr_time, start_time, curr_path)

app.title = "阿尔法-中信-股衍 实时交易监控"
app.layout = html.Div([
    html.Div([
        html.A(
            '进取2号',
            href='http://192.168.1.234:8052',
            # target='_self',  # 同窗口跳转，写或不写都可以
            style={
                'color': '#0366d6', 'fontWeight': '600',
                'textDecoration': 'none', 'fontSize': '18px',
                'marginRight': '12px'
            }
        ),
        html.A(
            '屿阔',
            href='http://192.168.1.234:8053',
            # target='_self',
            style={
                'color': '#0366d6', 'fontWeight': '600',
                'textDecoration': 'none', 'fontSize': '18px'
            }
        ),
        html.A(
            '进取3号',
            href='http://192.168.1.234:8054',
            # target='_self',
            style={
                'color': '#0366d6', 'fontWeight': '600',
                'textDecoration': 'none', 'fontSize': '18px',
                'marginLeft': '12px'
            }
        ),
    ],
        style={
            'position': 'fixed',
            'top': '8px',
            'left': '12px',
            'zIndex': 9999,
            'background': 'rgba(255,255,255,0.85)',
            'padding': '4px 10px',
            'borderRadius': '6px',
            'boxShadow': '0 2px 6px rgba(0,0,0,0.15)'
        }
    ),
    html.H1("阿尔法-中信-股衍 实时交易监控",
            style={'text-align': 'center', 'margin-top': '20px'}),
    html.H2(id='progress-text', style={'text-align': 'center', 'margin-bottom': '16px'}),
    html.Div(id='startup-warning', style={'color': 'red', 'text-align': 'center', 'font-size': '24px', 'margin-bottom': '20px'}),
    html.Div([
        html.Div([
            html.Label('Turn Include Stocks:', style={
                'display': 'inline-block', 'margin-right': '10%'}),
            dcc.Dropdown(
                id='turn-option-selector',
                options=stock_options,  # 使用动态生成的选项列表
                multi=True,
                style={'display': 'inline-block', 'width': '60%'}
            ),
            dcc.Graph(id='live-update-graph1'),
            dcc.Graph(id='chg-graph'),
            dcc.Graph(id='leverage-graph'),
        ], style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'top'}),
        html.Div([
            html.Div([
                html.Label('Dev Exclude Stocks:', style={
                           'display': 'inline-block', 'margin-right':  '10%'}),
                dcc.Checklist(
                    id='dev-option-selector',
                    options=[
                        {'label': 'Exclude Buy', 'value': 'buy'},
                        {'label': 'Exclude Sell', 'value': 'sell'}
                    ],
                    value=['buy', 'sell'],  # 默认选择
                    inline=True,
                    style={'display': 'inline-block', 'margin-right': '20%'}
                ),
                dcc.Dropdown(
                    id='dev-exclude-selector',
                    options=stock_options,  # 使用动态生成的选项列表
                    multi=True,
                    style={'display': 'inline-block', 'width': '60%'}
                )
            ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'flex-start', 'margin-bottom': '10px'}),
            dcc.Graph(id='live-update-graph4')
        ], style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'top'}),
        html.Div([dcc.Graph(id='live-update-graph2', style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'top'}),
                  dcc.Graph(id='live-update-graph3', style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'top'})]),
        dash_table.DataTable(id='data-table',
                             columns=[{'name': '代码', 'id': '代码', 'type': 'text'},

                                      # 当前数量列为整数
                                      {'name': '当前数量', 'id': '当前数量', 'type': 'numeric', 'format': {
                                          'specifier': 'd'}},

                                      # 当前市值列保留两位小数
                                      {'name': '当前市值', 'id': '当前市值', 'type': 'numeric', 'format': {
                                          'specifier': '.2f'}},

                                      # 百分比列，保留两位小数并以百分号结尾
                                      {'name': '2倍目标数量', 'id': '2倍目标数量', 'type': 'numeric', 'format': {
                                          'specifier': '.2%'}},
                                      # 根据数据框的列动态生成列名
                                      {'name': '开盘目标数量', 'id': '开盘目标数量', 'type': 'numeric', 'format': {'specifier': '.2%'}}],
                             data=target_df.to_dict(
                                 'records'),  # 将数据框内容转换为字典形式
                             page_size=130,  # 每页展示的行数
                             filter_action="native",  # 启用筛选功能
                             sort_action="native",
                             style_data_conditional=[  # 设置条件样式
                                 {
                                         'if': {
                                             # 选择条件
                                             'filter_query': '{2倍目标数量} > 0.005 or {2倍目标数量} < -0.005',
                                         },
                                     'backgroundColor':"rgba(109,152,190,0.5)",
                                     'color': 'red',
                                 },
                             ],
                             style_table={'width': '61.8%',
                                          'margin': '0 auto'},  # 设置表格宽度和居中样式
                             style_cell={  # 控制单元格样式
                                 'textAlign': 'center',  # 居中对齐内容
                                 'whiteSpace': 'normal',
                                 'height': 'auto',
                             },
                             )

    ], style={'width': '100%'}),
    dcc.Interval(
        id='interval-component',
        interval=1 * 30000,  # 更新间隔，单位为毫秒，这里是60秒
        n_intervals=0
    ),

])

def create_individual_figure(file_path, buy, sell, selected_stocks, title):
    df = pd.read_csv(file_path, index_col=0)
    df.index = [i[:-3] for i in df.index]
    df.fillna(0, inplace=True)

    fig = go.Figure()
    for stk in buy[title]:
        stk = stk[2:] + '.' + stk[:2]
        if stk in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[stk], mode='lines', name=stk, line=dict(color="#D37440")))

    for stk in sell[title]:
        stk = stk[2:] + '.' + stk[:2]
        if stk in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[stk], mode='lines', name=stk, line=dict(color='#0070C0')))

    for stk in selected_stocks:
        if stk in df.columns:
            start_value = df[stk].iloc[0]
            end_value = df[stk].iloc[-1]
            if end_value > start_value:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df[stk], mode='lines', name=stk, linee=dict(color="#D37440")))
            else:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df[stk], mode='lines', name=stk, line=dict(color='#0070C0')))

    fig.update_yaxes(title_text="Individual Stock Value")
    fig.update_xaxes(tickangle=90)

    fig.update_layout(height=600, width=1200,
                      title_text=f"换仓数据", showlegend=False)

    return fig


def create_total_figure(file_path):
    df = pd.read_csv(file_path, index_col=0)
    df['total'] = df.sum(axis=1)
    df.index = [i[:-3] for i in df.index]

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df.index, y=df['total'], mode='lines', name='total', line=dict(color="#0070C0"),
            fill="tonexty",
            fillcolor="rgba(109,152,190,0.5)",))

    if df.index[-1] < '09:35':
        fig.update_yaxes(title_text="Total Value")
        fig.update_xaxes(tickangle=90)
        fig.update_layout(height=600, width=1200,
                          title_text=f"总市值", showlegend=True)
        return fig

    df_after_930 = df.loc[df.index >= '09:31']
    max_total = df_after_930['total'].max()
    min_total = df_after_930['total'].min()
    delta = max_total - min_total

    fig.update_yaxes(title_text="Total Value", range=[
                     min_total - delta, max_total + delta])
    fig.update_xaxes(tickangle=90)

    fig.update_layout(height=600, width=1200,
                      title_text=f"总市值", showlegend=True)
    return fig


def create_average_figure(file_path):
    df = pd.read_csv(file_path, index_col=0)
    df['avg'] = df.apply(lambda row: row.sort_values().iloc[int(
        len(row) * 0.3):int(len(row) * 0.7)].mean(), axis=1)
    df.index = [i[:-3] for i in df.index]

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df.index, y=df['avg'], mode='lines', name='avg', line=dict(color="#0070C0"),
            fill="tonexty",
            fillcolor="rgba(109,152,190,0.5)",))

    if df.index[-1] < '09:35':

        fig.update_yaxes(title_text="avg Value")
        fig.update_xaxes(tickangle=90)

        fig.update_layout(height=600, width=1200,
                          title_text=f"均值", showlegend=True)
        return fig

    df_after_930 = df.loc[df.index >= '09:31']
    max_avg = df_after_930['avg'].max()
    min_avg = df_after_930['avg'].min()
    delta = max_avg - min_avg

    fig.update_yaxes(title_text="avg", range=[
                     min_avg - delta, max_avg + delta])
    fig.update_xaxes(tickangle=90)

    fig.update_layout(height=600, width=1200,
                      title_text=f"均值", showlegend=True)

    return fig

def create_deviation_figure(file_path, selected_stocks):
    def _hex_to_rgb(hex_color: str):
        c = hex_color.lstrip("#")
        return tuple(int(c[i : i + 2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(rgb: tuple[int, int, int]):
        return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"

    def _interpolate_hex(start_hex: str, end_hex: str, t: float):
        t = max(0.0, min(1.0, t))
        s = _hex_to_rgb(start_hex)
        e = _hex_to_rgb(end_hex)
        mixed = tuple(int(round(s[i] + (e[i] - s[i]) * t)) for i in range(3))
        return _rgb_to_hex(mixed)
    
    df = pd.read_csv(file_path, index_col=0)
    for stk in selected_stocks:
        try:
            df.drop(stk, axis=1, inplace=True)
        except:
            pass
    last_row = df.iloc[-1].sort_values()  # 取最后一行并仅展示所选股票

    # 计算中位数
    median_value = last_row.median()
    if median_value == 0:
        deviation = pd.Series(0.0, index=last_row.index)
    else:
        deviation = last_row / median_value - 1

    pos_max = deviation[deviation >= 0].max() if (deviation >= 0).any() else 0
    neg_min = deviation[deviation < 0].min() if (deviation < 0).any() else 0
    # 将数据调整为相对于中位数的偏差
    deviation_from_median = last_row / median_value-1

    fig = go.Figure()

    marker_color = []
    for v in deviation_from_median.values:
        print(v)
        if v >= 0.1:
            marker_color.append('#001042')
        elif v <= -0.1:
            marker_color.append('#001042')
        elif v > 0:
            t = (v / pos_max) if pos_max > 0 else 0
            marker_color.append(_interpolate_hex("#88A4CB", "#001042", t))
        else:
            t = (abs(v) / abs(neg_min)) if neg_min < 0 else 0
            marker_color.append(_interpolate_hex("#88A4CB", "#001042", t))

    fig.add_trace(
        go.Bar(
            y=last_row.index,
            x=deviation.values,
            orientation="h",
            marker_color=marker_color,
            text=[f"{v:.2%}" for v in deviation.values],
            textposition="auto",
        )
    )

    fig.update_xaxes(title_text="Deviation from Median Value",
                     zeroline=True, zerolinecolor='black')
    fig.update_yaxes(title_text="Stock")
    fig.update_layout(height=1800, width=1200,
                      showlegend=False)

    return fig

def create_chg_figure(chg_df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=chg_df['time'], y=chg_df['chg'], mode='lines', name='Change',line=dict(color="#0070C0"),))
    fig.update_layout(title=f"盈亏图表，当前盈亏：{chg_df['chg'].iloc[-1]:.2%}",
                      xaxis_title='Time', yaxis_title='Change')
    return fig


def create_leverage_figure(chg_df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=chg_df['time'], y=chg_df['leverage'], mode='lines', name='leverage',line=dict(color="#0070C0"),))
    fig.update_layout(title=f"杠杆图表，当前杠杆:{chg_df['leverage'].iloc[-1]}",
                      xaxis_title='Time', yaxis_title='Change')
    return fig


@app.callback([
    Output('live-update-graph1', 'figure'),
    Output('live-update-graph2', 'figure'),
    Output('live-update-graph3', 'figure'),
    Output('live-update-graph4', 'figure'),
    Output('chg-graph', 'figure'),
    Output('leverage-graph', 'figure'),
    Output('data-table', 'data'),
    Output('startup-warning', 'children'),
    Output('progress-text', 'children') ,# 新增买卖进度动态输出
],
    [Input('interval-component', 'n_intervals'),
     Input('turn-option-selector', 'value'),
     Input('dev-option-selector', 'value'),
     Input('dev-exclude-selector', 'value'), ])
def update_graph_live(n, turn_selected, dev_selected_option, dev_exclude_stocks):
    today, url, file_path, trade_file, order_file, chg_file, curr_path = get_today_files()
    try:
        sell, buy = get_trade_data(trade_file)
        df, stock_options = get_stock_options(file_path)
        names, times = get_times(curr_path)
        curr_time = times[0] if times else '093100'
        start_time = curr_time
        if curr_time >= '133100' and len(times) > 1:
            start_time = [time for time in times if time > '093100'][-1]
        dev_selected_stocks = []
        if 'buy' in dev_selected_option:
            dev_selected_stocks += [stk[2:] + '.' + stk[:2]
                                    for stk in buy.get(file_path[-6:-4], [])]
        if 'sell' in dev_selected_option:
            dev_selected_stocks += [stk[2:] + '.' + stk[:2]
                                    for stk in sell.get(file_path[-6:-4], [])]
        if dev_exclude_stocks:
            dev_selected_stocks += [stk for stk in dev_exclude_stocks]
        turn_selected_stocks = []
        if turn_selected:
            turn_selected_stocks = [stk for stk in turn_selected if stk in df.columns]
        updated_df, buy_process, sell_process = target_data_process(curr_time, start_time, curr_path)
        fig1 = create_individual_figure(
            file_path, buy, sell, turn_selected_stocks, file_path[-6:-4])
        fig2 = create_total_figure(file_path)
        fig3 = create_average_figure(file_path)
        fig4 = create_deviation_figure(file_path, dev_selected_stocks)
        fig_chg = create_chg_figure(pd.read_csv(chg_file, header=0))
        fig_leverage = create_leverage_figure(pd.read_csv(chg_file, header=0))
        progress_text = f"买进度：{buy_process:.2%}，卖进度：{sell_process:.2%}"
        warning = ''
        return fig1, fig2, fig3, fig4, fig_chg, fig_leverage, updated_df.to_dict('records'), warning, progress_text
    except Exception as e:
        import plotly.graph_objects as go
        empty_fig = go.Figure()
        progress_text = "买进度：-- 卖进度：--"
        warning = '当天还未启动'
        return empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, [], warning, progress_text
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8051, debug=False)