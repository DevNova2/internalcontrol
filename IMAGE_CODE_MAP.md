# 图片与代码对应索引

这个文件用于记录“截图 / 图片”和“项目代码位置”的对应关系，方便后续按图找代码。

## 记录规则

- 每次新增一张图，优先记录页面标题、截图特征、访问路径、核心视图、模板文件。
- 如果一个图片对应多个文件，按“入口视图 -> 模板 -> 相关路由 / 公共模板”的顺序记录。
- 如果页面需要登录、特定日期参数或其他访问条件，也一并写明。

***

## 1. 大A市值分布

### 截图特征

- 页面顶部文案包含：`大A市值分布 ~ 2025-01-13`
- 图表标题包含：`2025-01-13 全市场 5125 只票，市值分布直方图`
- 横轴标题包含：`市值（单位：亿元）`
- 图中有两组分布：`累计分布`、`市值分布`

### 页面访问路径

- 本地地址：`/stra/cap_dist/2025-01-13`
- 完整示例：`http://127.0.0.1:8000/stra/cap_dist/2025-01-13`

### 关联代码

- 核心视图：[views.py -](file:///Users/w/Desktop/internalcontrol/Internal_System/mult_factor/views.py#L55-L77) [`mkt_cap_hist()`](file:///Users/w/Desktop/internalcontrol/Internal_System/mult_factor/views.py#L55-L77)
- 路由定义：[urls.py](file:///Users/w/Desktop/internalcontrol/Internal_System/mult_factor/urls.py#L15-L20)
- 项目主路由挂载：[urls.py](file:///Users/w/Desktop/internalcontrol/Internal_System/urls.py#L21-L34)
- 页面模板：[cap\_dist.html](file:///Users/w/Desktop/internalcontrol/Internal_System/mult_factor/templates/mult_factor/cap_dist.html)
- 公共模板：[base.html](file:///Users/w/Desktop/internalcontrol/Internal_System/templates/base.html)

### 代码对应说明

- `mkt_cap_hist()` 从数据库读取指定日期的 `mkt_cap_ard` 数据。
- 视图里使用 Plotly 生成两个直方图：
  - `累计分布`
  - `市值分布`
- 图表标题、横轴标题都在这个函数里直接拼接生成。
- `cap_dist.html` 只负责承载 `fig` 的 HTML 输出，本身不生成图。

### 访问说明

- 页面需要先登录。
- 当前本地验证可用账号：
  - 用户名：`neo`
- 本地调试时如果出现 `base.html` 缺失，检查公共模板文件是否存在。
- <br />

***

## 2. 可变阿尔法一号

### 截图特征

- 页面顶部导航包含：`实盘（可变阿一号）`
- 主图标题包含：`可变阿尔法一号（2019-01-08 ~ 2024-11-29），累计收益：259.53%，年化收益：25.30%`
- 下方图标题包含：`可变阿尔法一号（2019-01-08 ~ 2024-11-29） - 月胜率：60.56% ~ 月盈亏比：1.45`
- 页面连续展示两张 Plotly 图：上方为`累计净值/回撤`，下方为`月度收益热力图`

### 页面访问路径

- 本地地址：`/firm_offer/index/SEY112`
- 完整示例：`http://127.0.0.1:8000/firm_offer/index/SEY112`

### 关联代码

- 核心视图：[views.py - `firm_index()`](file:///Users/w/Desktop/internalcontrol/Internal_System/firm_offer/views.py#L121-L145)
- 净值与回撤图生成：[views.py - `_plot_net_back()`](file:///Users/w/Desktop/internalcontrol/Internal_System/firm_offer/views.py#L22-L43)
- 月胜率热力图生成：[views.py - `_plot_hot_map()`](file:///Users/w/Desktop/internalcontrol/Internal_System/firm_offer/views.py#L69-L118)
- 路由定义：[urls.py](file:///Users/w/Desktop/internalcontrol/Internal_System/firm_offer/urls.py#L14-L19)
- 页面模板：[index.html](file:///Users/w/Desktop/internalcontrol/Internal_System/firm_offer/templates/firm_offer/index.html)
- 公共模板：[base.html](file:///Users/w/Desktop/internalcontrol/Internal_System/templates/base.html)

### 代码对应说明

- `firm_index()` 根据 `pro_id` 选择产品；当 `pro_id == 'SEY112'` 时，产品名就是 `可变阿尔法一号`。
- `firm_index()` 从 `product.net_value_alpha_first` 读取净值数据，并生成两类图：
  - `_plot_net_back()`：累计净值与回撤
  - `_plot_hot_map()`：月胜率与月盈亏比热力图
- 页面模板 `firm_offer/index.html` 负责按顺序渲染 `net_back`、`net_sst`、`chg_detail` 三块内容。

### 访问说明

- 当前本地访问已验证可直接打开该页。
- 如果后续被登录拦截，可使用：
  - 用户名：`neo`
  - 密码：`admin`

***

## 3. 阿尔法1号与基准指数累计净值对比

### 截图特征

- 图例包含：`阿尔法1号累计净值`
- 对比基准包含：`沪深300指数累计净值`
- 截图另一张同类图展示：`万得微盘指数累计净值`
- 页面样式更像 HoloViews / Bokeh 交互图，右侧带工具栏与图例

### 页面访问路径

- 当前仓库中未发现已挂载到 Django 的直接访问路径
- 相关代码属于旧的独立可视化脚本链路，不是当前 `firm_offer` 这类现成页面

### 关联代码

- 核心对比逻辑：[vis_alpha_one.py - `__load_by_bench()`](file:///Users/w/Desktop/internalcontrol/Internal_System/dq_alpha_one/vis_alpha_one.py#L152-L201)
- 页面生成入口：[vis_alpha_one.py - `html_alpha_more_value()`](file:///Users/w/Desktop/internalcontrol/Internal_System/dq_alpha_one/vis_alpha_one.py#L203-L211)
- Alpha 数据读取：[load_data.py - `get_alpha_one()`](file:///Users/w/Desktop/internalcontrol/Internal_System/Datas/load_data.py#L215-L224)
- 基准数据读取：[load_data.py - `get_dates_bench_chg()`](file:///Users/w/Desktop/internalcontrol/Internal_System/Datas/load_data.py#L226-L235)
- `dq_alpha_one` 路由占位：[urls.py](file:///Users/w/Desktop/internalcontrol/Internal_System/dq_alpha_one/urls.py#L15-L17)

### 代码对应说明

- `__load_by_bench()` 会把阿尔法一号累计涨幅与基准指数做叠加对比，并计算超额收益。
- 当前代码里明确支持的基准是：
  - `沪深300`
  - `中证500`
- 截图中的“沪深300指数累计净值”与这段代码高度对应。
- 截图中的“万得微盘指数累计净值”在当前仓库里没有搜到同名字段，更像同一类旧图在其他环境或后续版本里的基准切换结果。

### 访问说明

- 当前本地仓库里能定位到相关代码，但没有现成可直接访问的 Django 页面。
- 我已尝试仅用运行时补丁启动这条旧链路，但当前本地环境还存在旧配置和旧数据结构依赖，暂时不能直接预览。

***

## 4. 阿尔法1号分时损失拟合

### 截图特征

- 页面顶栏文案包含：`佣啥策略分时研究报告 ~ 交易日 2024-12-31`
- 左右两张图标题都含：`2024-12-31 ~ 阿尔法1号`
- 图中图例包含：`sell`、`buy`、`differ`
- 标题文案含：`多头_损失拟合`、`空头_损失拟合`

### 页面访问路径

- 路由入口：`/trade_detail/pro_trade_detail/`
- 完整示例：`http://127.0.0.1:8000/trade_detail/pro_trade_detail/`

### 关联代码

- 页面入口视图：[views.py - `index_stra_detail()`](file:///Users/w/Desktop/internalcontrol/Internal_System/trade_detail/views.py#L528-L555)
- 图表组装逻辑：[views.py - `_return_df()`](file:///Users/w/Desktop/internalcontrol/Internal_System/trade_detail/views.py#L492-L510)
- 标题与折线生成：[views.py - `_plot()`](file:///Users/w/Desktop/internalcontrol/Internal_System/trade_detail/views.py#L442-L489)
- `differ` 计算：[views.py - `calculate_difference()`](file:///Users/w/Desktop/internalcontrol/Internal_System/trade_detail/views.py#L513-L525)
- 路由定义：[urls.py](file:///Users/w/Desktop/internalcontrol/Internal_System/trade_detail/urls.py#L16-L20)
- 页面模板：[index_stra.html](file:///Users/w/Desktop/internalcontrol/Internal_System/trade_detail/templates/trade_detail/index_stra.html)

### 代码对应说明

- `index_stra_detail()` 会读取阿尔法 1 号和屿阔 1 号的分钟数据。
- 对阿尔法 1 号，视图会生成三组图：
  - `fig_index_a`：指数拟合
  - `fig_buy_a`：换入
  - `fig_sell_a`：换出
- `_plot()` 中直接绘制 `buy`、`sell`、`differ` 三条线，图例与截图一致。
- 标题里的 `多头/空头_损失拟合` 属于这一页分时研究图的一类展示文案，和这条逻辑高度对应。

### 访问说明

- 当前截图对应代码可以明确定位到。
- 这页是当前 Django 已挂载页面，可直接通过 `/trade_detail/pro_trade_detail/` 访问最新交易日数据。
- 截图中的 `2024-12-31` 是当时页面数据日期；当前本地打开时显示的可能是库里最新日期。

***

## 5. 股价交易缺失分析

### 截图特征

- 浏览器标签文案包含：`股价交易缺失分析`
- 页面标题包含：`股价模型不剔除财报披露日 - 指数拟合`
- 标题日期区间类似：`2024-11-22 ~ 2024-12-31`
- 图内主线条为红、灰、蓝三条，页面右上角下拉菜单中高亮 `股价交易缺失分析`

### 页面访问路径

- 当前最接近入口：`/trade_detail/pro_trade_detail/`
- 完整示例：`http://127.0.0.1:8000/trade_detail/pro_trade_detail/`

### 关联代码

- 页面入口视图：[views.py - `index_stra_detail()`](file:///Users/w/Desktop/internalcontrol/Internal_System/trade_detail/views.py#L528-L555)
- 图表绘制：[views.py - `_plot()`](file:///Users/w/Desktop/internalcontrol/Internal_System/trade_detail/views.py#L442-L489)
- 图表组装：[views.py - `_return_df()`](file:///Users/w/Desktop/internalcontrol/Internal_System/trade_detail/views.py#L492-L510)
- 差值计算：[views.py - `calculate_difference()`](file:///Users/w/Desktop/internalcontrol/Internal_System/trade_detail/views.py#L513-L525)
- 路由定义：[urls.py](file:///Users/w/Desktop/internalcontrol/Internal_System/trade_detail/urls.py#L16-L20)
- 页面模板：[index_stra.html](file:///Users/w/Desktop/internalcontrol/Internal_System/trade_detail/templates/trade_detail/index_stra.html)

### 代码对应说明

- 当前仓库里没有直接搜到 `股价交易缺失分析` 这几个字的源码文案。
- 但截图中的主图形态、`指数拟合` 标题、三条线结构，以及阿尔法 1 号相关分时分析，和 `trade_detail` 里的 `index_stra_detail()` 这条页面逻辑高度对应。
- 因此这张图大概率是该页面在某个版本或菜单命名下的展示结果。

### 访问说明

- 当前本地验证时，这个入口会进入后端视图，但实际打开报错：`KeyError: 'date'`。
- 结论是：相关代码有，高度疑似就是这条页面；但当前本地不能正常打开成业务图表页。

***

## 6. 股价交易损失分析

### 截图特征

- 页面标题包含：`股价交易损失分析 ~ 交易日：2025-01-07`
- 页面主体连续展示多张 Plotly 图
- 图例包含多组 `turn`、`reb`、`all` 相关曲线
- 右侧图例中可见 `ma20`、`ma5` 等移动平均字样

### 页面访问路径

- 路由入口：`/trade_loss/loss_detail/<pro>`
- 完整示例：`http://127.0.0.1:8000/trade_loss/loss_detail/MARGIN`

### 关联代码

- 页面入口视图：[views.py - `loss_index()`](file:///Users/w/Desktop/internalcontrol/Internal_System/TradeLoss/views.py#L83-L115)
- 图表封装类：[views_plotly.py - `PlotLoss`](file:///Users/w/Desktop/internalcontrol/Internal_System/TradeLoss/views_plotly.py#L23-L243)
- 总体损失趋势图：[views_plotly.py - `plot_all_area()`](file:///Users/w/Desktop/internalcontrol/Internal_System/TradeLoss/views_plotly.py#L113-L170)
- 最近 N 日损失图：[views_plotly.py - `plot_latest_days()`](file:///Users/w/Desktop/internalcontrol/Internal_System/TradeLoss/views_plotly.py#L172-L203)
- 周 / 月频损失图：[views_plotly.py - `plot_latest_freq()`](file:///Users/w/Desktop/internalcontrol/Internal_System/TradeLoss/views_plotly.py#L205-L243)
- 路由定义：[urls.py](file:///Users/w/Desktop/internalcontrol/Internal_System/TradeLoss/urls.py#L15-L18)
- 项目主路由挂载：[urls.py](file:///Users/w/Desktop/internalcontrol/Internal_System/ShuiDQReport/urls.py#L25)

### 代码对应说明

- `loss_index()` 会一次性生成多张损失分析图，包括：
  - `fig_all`
  - `fig_all_twap`
  - `fig_latest`
  - `fig_latest_twap`
  - `html_weekly`
  - `html_weekly_twap`
  - `html_monthly`
  - `html_monthly_twap`
- `plot_all_area()` 标题里直接拼接 `MEAN(all)`、`MEAN(reb)`、`MEAN(turn)` 与 `MA20(all)`、`MA20(reb)`、`MA20(turn)`，和截图风格高度一致。
- 这张图对应的是 `TradeLoss` 模块的损失分析页，不是 `trade_detail` 那条分时详情页。

### 访问说明

- 当前仓库里可以明确定位到后端视图、图表生成逻辑和路由。
- 但 `views.py` 引用的模板 `TradeLoss/index.html`、`TradeLoss/pro_list.html` 在当前仓库里未找到，因此本地暂时不能像其他页面一样直接预览。

***

## 7. 产品(@1号) 损失分析

### 截图特征

- 页面标题包含：`产品(@1号) ~ 参照第一笔订单发生时刻 ~ 2025-01-10`
- 第二张图标题包含：`产品(@1号) ~ 交易时段TWAP（分钟成交量加权） ~ 2025-01-10`
- 图例包含：`Turn(MA=20)`、`Reb(MA=20)`、`All(MA=20)`、`Turn`、`Reb`、`所有订单`
- 标题正文包含：`MEAN(all)`、`MEAN(reb)`、`MEAN(turn)` 与 `MA20(all)`、`MA20(reb)`、`MA20(turn)`

### 页面访问路径

- 路由入口：`/trade_loss/loss_detail/ALPHA_ALL`
- 完整示例：`http://127.0.0.1:8001/trade_loss/loss_detail/ALPHA_ALL`

### 关联代码

- 页面入口视图：[views.py - `loss_index()`](file:///Users/w/Desktop/internalcontrol/Internal_System/TradeLoss/views.py#L83-L115)
- 产品参数映射：[views_plotly.py - `PlotLoss.__init__()`](file:///Users/w/Desktop/internalcontrol/Internal_System/TradeLoss/views_plotly.py#L23-L55)
- 总体损失趋势图：[views_plotly.py - `plot_all_area()`](file:///Users/w/Desktop/internalcontrol/Internal_System/TradeLoss/views_plotly.py#L113-L170)
- 最近 N 日损失图：[views_plotly.py - `plot_latest_days()`](file:///Users/w/Desktop/internalcontrol/Internal_System/TradeLoss/views_plotly.py#L172-L203)
- 周 / 月频损失图：[views_plotly.py - `plot_latest_freq()`](file:///Users/w/Desktop/internalcontrol/Internal_System/TradeLoss/views_plotly.py#L205-L243)
- 路由定义：[urls.py](file:///Users/w/Desktop/internalcontrol/Internal_System/TradeLoss/urls.py#L15-L18)
- 页面模板：[index.html](file:///Users/w/Desktop/internalcontrol/Internal_System/templates/TradeLoss/index.html)

### 代码对应说明

- 当 `pro == 'ALPHA_ALL'` 时，`PlotLoss` 会把产品名映射成 `产品(@1号)`，并读取集合 `statistic.loss_alpha_all`。
- `plot_all_area()` 会直接生成截图里这种包含 `MEAN(...)` 和 `MA20(...)` 文案的面积图 / 均线图。
- 同一页面会连续渲染“参照第一笔订单发生时刻”和“交易时段TWAP（分钟成交量加权）”两类图，和截图布局一致。

### 访问说明

- 当前本地已验证可以正常打开。
- 这张图建议使用 `8001` 端口访问，因为该端口运行的是最新模板和最新服务进程。

***

## 后续追加模板

复制下面这一段，后续每确认一张图就补一条：

```md
## N. 图片名称

### 截图特征

- 页面顶部文案：
- 图表标题：
- 横轴 / 纵轴关键字：
- 其他可识别特征：

### 页面访问路径

- 本地地址：
- 完整示例：

### 关联代码

- 核心视图：
- 路由定义：
- 页面模板：
- 相关脚本 / 组件：
- 公共模板：

### 代码对应说明

- 

### 访问说明

- 
```
