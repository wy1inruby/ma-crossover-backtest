"""
均线策略回测 —— 第一个量化小项目
Moving Average Crossover Backtest

策略：短期均线（20 日）上穿长期均线（60 日）时买入持有，下穿时卖出空仓。
对比"一直持有"(Buy & Hold) 看策略有没有用。

运行前先安装：pip install yfinance pandas matplotlib
"""

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# ========== 第 1 步：参数（可以自己改着玩）==========
TICKER = "002028.SZ"     # 思源电气（深交所 002028）。深市加 .SZ，沪市加 .SS
START = "2018-01-01"
END = "2025-12-31"
SHORT_WIN = 20           # 短期均线天数
LONG_WIN = 60            # 长期均线天数

# ========== 第 2 步：下载历史数据 ==========
data = yf.download(TICKER, start=START, end=END, auto_adjust=True)
if isinstance(data.columns, pd.MultiIndex):   # 新版 yfinance 列是两层，压成一层
    data.columns = data.columns.get_level_values(0)
df = data[["Close"]].copy()
print(df.head())         # 先看看数据长什么样

# ========== 第 3 步：算每日收益率 ==========
# pct_change() = (今天价格 / 昨天价格) - 1
df["return"] = df["Close"].pct_change()

# ========== 第 4 步：算均线 ==========
# rolling(n).mean() = 过去 n 天收盘价的平均
df["ma_short"] = df["Close"].rolling(SHORT_WIN).mean()
df["ma_long"] = df["Close"].rolling(LONG_WIN).mean()

# ========== 第 5 步：生成交易信号 ==========
# 短均线在长均线上方 -> 1（持仓），否则 -> 0（空仓）
df["signal"] = (df["ma_short"] > df["ma_long"]).astype(int)
# 重要：今天收盘才知道信号，所以明天才能交易 -> shift(1)，避免"偷看未来"
df["position"] = df["signal"].shift(1)

# ========== 第 6 步：算策略收益 ==========
df["strategy_return"] = df["position"] * df["return"]
df = df.dropna()

# 累计收益：(1+r1)*(1+r2)*...
df["cum_buyhold"] = (1 + df["return"]).cumprod()
df["cum_strategy"] = (1 + df["strategy_return"]).cumprod()

# ========== 第 7 步：评价指标 ==========
def summary(returns, name):
    total = (1 + returns).prod() - 1
    years = len(returns) / 252                       # 一年约 252 个交易日
    annual = (1 + total) ** (1 / years) - 1          # 年化收益
    vol = returns.std() * 252 ** 0.5                 # 年化波动率
    sharpe = annual / vol if vol > 0 else float("nan")  # 夏普比率（简化版，未扣无风险利率）
    cum = (1 + returns).cumprod()
    max_dd = (cum / cum.cummax() - 1).min()          # 最大回撤：从高点最多跌了多少
    print(f"{name:12s} 总收益 {total:7.1%} | 年化 {annual:6.1%} | "
          f"波动 {vol:5.1%} | 夏普 {sharpe:4.2f} | 最大回撤 {max_dd:6.1%}")

print()
summary(df["return"], "Buy & Hold")
summary(df["strategy_return"], "MA Strategy")
print(f"交易次数：{int(df['position'].diff().abs().sum())}")

# ========== 第 8 步：画图 ==========
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

ax1.plot(df.index, df["Close"], label="Close", linewidth=1)
ax1.plot(df.index, df["ma_short"], label=f"MA{SHORT_WIN}", linewidth=1)
ax1.plot(df.index, df["ma_long"], label=f"MA{LONG_WIN}", linewidth=1)
ax1.set_title(f"{TICKER} price and moving averages")
ax1.legend()

ax2.plot(df.index, df["cum_buyhold"], label="Buy & Hold")
ax2.plot(df.index, df["cum_strategy"], label="MA Strategy")
ax2.set_title("Cumulative return (start = 1)")
ax2.legend()

plt.tight_layout()
plt.savefig("backtest_result.png", dpi=150)
plt.show()
