from dash import Dash, html, dcc, Input, Output
import pandas as pd
import pymongo
import datetime

url = 'mongodb://192.168.1.77:27017/'

client = pymongo.MongoClient(url)

date_db = pymongo.MongoClient(
    'mongodb://Tom:tom@192.168.1.99:29900/?authSource=admin&readPreference=primary&ssl=false&directConnection=true')
date_col = date_db['economic']['trade_dates']

def get_all_dates():
    today = datetime.date.today().strftime('%Y-%m-%d')
    all_dates = sorted(
        [item['trade_date'] for item in date_col.find(
            {'trade_date': {"$lte": today}}, {'trade_date': 1, '_id': 0})],
        reverse=True
    )
    return all_dates

# 创建 Dash 应用
app = Dash(__name__)

# 获取所有日期和产品名称
all_products = {
    '进取一号': {
        'code': 'jq1',
        'colors': {
            'header': '#9F2323',
            'row_odd': '#F2F2F2',
            'highlight': '#FBE3C1'
        },
    },
    '进取二号': {
        'code': 'jq2',
        'colors': {
            'header': '#AB6500',
            'row_odd': '#F2F2F2',
            'highlight': '#FBE3C1'
        },
    },
    '进取三号': {
        'code': 'jq3',
        'colors': {
            'header': '#AB6500',
            'row_odd': '#F2F2F2',
            'highlight': '#FBE3C1'
        },
    },
    '屿阔一号': {
        'code': 'yk1',
        'colors': {
            'header': '#4A4A4A',
            'row_odd': '#EFEFEF',
            'highlight': '#D0D0D0'
        },
    },
    '香港产品':{
        "code":'hk1',
        'colors': {
            'header': "#FF0000",
            'row_odd': '#F2F2F2',
            'highlight': '#FBE3C1'
        },
    },
    # 可以在此添加其他产品及其配色
}
col = None

# 设置默认日期和产品
all_dates = get_all_dates()
default_date = all_dates[1] if len(all_dates) > 1 else all_dates[0]
default_product = '进取一号'


@app.callback(
    Output('date-picker', 'min_date_allowed'),
    Output('date-picker', 'max_date_allowed'),
    Output('date-picker', 'date'),
    Input('interval-component', 'n_intervals')
)
def update_date_picker(n):
    all_dates = get_all_dates()
    min_date = min(pd.to_datetime(all_dates))
    max_date = max(pd.to_datetime(all_dates))
    default_date = all_dates[1] if len(all_dates) > 1 else all_dates[0]
    return min_date, max_date, default_date


@app.callback(
    Output('output-content', 'children'),
    [Input('date-picker', 'date'),
     Input('product-dropdown', 'value')]
)
def update_content(selected_date, selected_product):
    global col
    if not selected_date or not selected_product:
        return html.Div("请先选择日期和产品。")

    # 根据选取的产品动态改变集合
    product_info = all_products[selected_product]
    col = client['product_detail'][product_info['code']]

    # 查询数据库，仅根据日期查询
    data = list(col.find({'date': selected_date}))
    if not data:
        return html.Div("未找到相关数据。")

    data = data[0]
    dics = []
    for key, value in data.items():
        if type(value) == dict and 'net_asset' in value:
            dics.append(value)

    # 对 dics 列表排序
    dics = sorted(dics, key=lambda x: {
        'stock': 0, 'fund': 3, 'cash': 4, 'future': 1, 'repurchase': 2}.get(x['type'], 3))
    original_data = []
    for dic in dics:
        entry = {
            "账户类型": dic['name'],
            "今日市值": f"{dic['total_asset']:,.2f}",
            "净资产": f"{dic['net_asset']:,.2f}",
            "盈亏金额": f"{dic['profit']:,.2f}" if 'profit' in dic and dic['profit'] is not None else '-',
            "涨跌幅": f"{dic['chg']:.4%}" if 'chg' in dic and dic['chg'] is not None else '-'
        }

        original_data.append(entry)
    leverage = data['leverage']
    total_net_asset = data['total_net_asset']
    total_asset = data['total_asset']
    profit = data['profit']
    net_unit_asset = data['net_unit_asset']
    chg = data['chg']
    last_net_unit_asset = data['last_net_unit_asset']

    try:
        huilv = data['huilv']
        total_data = {'整体杠杆': f"{leverage:.4f}", '汇率': f'{huilv:.4f}', 'Total_今日净资产': f"{total_net_asset:,.2f}", 'Total_今日市值': f"{total_asset:,.2f}", 'Total_盈亏金额': f"{profit:,.2f}",
                  'Total_涨跌幅': f"{chg:.4%}", '前日单位净值': f'{last_net_unit_asset:.4f}', '今日单位净值': f'{net_unit_asset:.4f}'}
    except:

        total_data = {'整体杠杆': f"{leverage:.4f}", 'Total_今日净资产': f"{total_net_asset:,.2f}", 'Total_今日市值': f"{total_asset:,.2f}", 'Total_盈亏金额': f"{profit:,.2f}",
                  'Total_涨跌幅': f"{chg:.4%}", '前日单位净值': f'{last_net_unit_asset:.4f}', '今日单位净值': f'{net_unit_asset:.4f}'}

    # 将数据横置（行转列）
    data = pd.DataFrame(original_data).set_index("账户类型").T.reset_index()
    data = data.rename(columns={"index": "指标"})  # 重命名第一列为“指标”
    # 表格布局
    return html.Div([
        html.H3(f"{selected_product} 收益统计 {selected_date}", style={
                "textAlign": "center", "color": product_info['colors']['header'], "width": "100%", "font-size": "30px"}),
        html.Div([
            html.Div([
                html.Table(
                    [
                        # 表头
                        html.Tr([html.Th(col, style={
                                "backgroundColor": product_info['colors']['header'], "color": "white", "padding": "10px"}) for col in ["指标", account]]),
                        # 表格数据
                        *[
                            html.Tr([html.Td(data.iloc[i]["指标"], style={
                                    "padding": "10px", "textAlign": "center", "backgroundColor": product_info['colors']['row_odd']}),
                                html.Td(data.iloc[i][account], style={
                                        "padding": "10px", "textAlign": "center"})])
                            for i in range(len(data))
                        ]
                    ],
                    style={"width": "100%",
                           "borderCollapse": "collapse", "margin": "auto"}
                )
            ], style={"width": "45%", "margin": "10px", "display": "inline-block"})
            for account in data.columns if account != "指标"
        ], style={"textAlign": "center", "width": "100%"}),
        html.Div([
            html.Table(
                [
                    # 表头
                    html.Tr([html.Th("指标", style={
                            "backgroundColor": product_info['colors']['header'], "color": "white", "padding": "10px"}),
                        html.Th("数值", style={
                                "backgroundColor": product_info['colors']['header'], "color": "white", "padding": "10px"})]),
                    # 表格数据
                    *[
                        html.Tr([html.Td(key, style={
                                "padding": "10px", "textAlign": "center", "backgroundColor": product_info['colors']['row_odd']}),
                            html.Td(value, style={
                                    "padding": "10px", "textAlign": "center", "backgroundColor": product_info['colors']['highlight'] if i == len(total_data) - 1 else ""})])
                        for i, (key, value) in enumerate(total_data.items())
                    ]
                ],
                style={"width": "91.5%",
                       "borderCollapse": "collapse", "margin": "auto"}
            )
        ], style={"textAlign": "center", "width": "100%", "margin": "10px", "display": "inline-block"})
    ], style={"display": "flex", "flexWrap": "wrap", "justifyContent": "center"})


# 应用布局
app.layout = html.Div([
    html.H3("产品收益统计", style={
        "textAlign": "center", "color": "#000000", "width": "100%", "font-size": "30px"}),

    # 日期选择器
    html.Div([
        html.Label("选择日期:", style={"margin-right": "10px"}),
        dcc.DatePickerSingle(
            id='date-picker',
            min_date_allowed=min(pd.to_datetime(all_dates)),
            max_date_allowed=max(pd.to_datetime(all_dates)),
            date=default_date,  # 设置默认日期
            display_format='YYYY-MM-DD'
        )
    ], style={"textAlign": "center", "margin": "10px"}),

    # 产品选择下拉框
    html.Div([
        html.Label("选择产品:", style={"margin-right": "10px"}),
        dcc.Dropdown(
            id='product-dropdown',
            options=[{'label': product, 'value': product}
                     for product in all_products],
            value=default_product,  # 设置默认产品
            style={"width": "50%", "margin": "auto"}
        )
    ], style={"textAlign": "center", "margin": "10px"}),

    # 表格和统计数据
    html.Div(id='output-content',
             style={"textAlign": "center", "width": "100%"}),
    # dcc.Interval(
    #     id='interval-component',
    #     interval=60*1000,  # 每分钟检查一次
    #     n_intervals=0
    # )
])

# 回调函数更新内容


# 运行应用
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=False)
