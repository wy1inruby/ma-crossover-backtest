"""
多只股票均线策略回测 —— 第二版
检验这个策略是否普遍有效

improvements：
1. 一次测试自选股里的 8 只股票/ETF
2. 扣除手续费（每次买或卖扣 0.1%）
3. 把数据切成两段：
   - "练习段" 2018-2022：设计策略时可以看的数据
   - "考试段" 2023-至今：假装设计时没见过，用来检验策略是不是真的有用
   如果只在练习段好、考试段差，就说明是过拟合

运行：/usr/local/bin/python3.13 multi_backtest.py
"""

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# ========== 第 1 步：参数 ==========
# 自选股 沪市代码加 .SS，深市加 .SZ
STOCKS = {
    "600436.SS": "片仔癀",
    "600519.SS": "贵州茅台",
    "601899.SS": "紫金矿业",
    "600660.SS": "福耀玻璃",
    "002028.SZ": "思源电气",
    "000938.SZ": "紫光股份",
    "002514.SZ": "ST宝馨",
    "159857.SZ": "光伏ETF",
}
START = "2018-01-01"
SPLIT = "2023-01-01"     # 这一天之前是练习段，之后是考试段
SHORT_WIN = 20
LONG_WIN = 60
FEE = 0.001              # 手续费 0.1%（每买一次或卖一次都扣）


# ========== 第 2 步：对一只股票做回测，返回每天的收益 ==========
def backtest(ticker):
    data = yf.download(ticker, start=START, auto_adjust=True, progress=False)
    if data.empty:
        return None
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    df = data[["Close"]].copy()
    df["return"] = df["Close"].pct_change()                  # 每天涨跌幅
    df["ma_short"] = df["Close"].rolling(SHORT_WIN).mean()   # 20 日均价
    df["ma_long"] = df["Close"].rolling(LONG_WIN).mean()     # 60 日均价

    # 短均价 > 长均价 -> 持有(1)，否则空仓(0)；第二天才能操作 -> shift(1)
    df["position"] = (df["ma_short"] > df["ma_long"]).astype(int).shift(1)
    df = df.dropna()

    # 仓位从 0 变 1（买入）或 1 变 0（卖出）的那天，扣一次手续费
    trades = df["position"].diff().abs().fillna(0)
    df["strategy_return"] = df["position"] * df["return"] - trades * FEE
    return df


# ========== 第 3 步：评价指标==========
def metrics(returns):
    if len(returns) < 20:
        return {}
    total = (1 + returns).prod() - 1
    years = len(returns) / 252
    annual = (1 + total) ** (1 / years) - 1
    vol = returns.std() * 252 ** 0.5
    sharpe = annual / vol if vol > 0 else float("nan")
    cum = (1 + returns).cumprod()
    max_dd = (cum / cum.cummax() - 1).min()
    return {"年化": annual, "夏普": sharpe, "最大回撤": max_dd}


# ========== 第 4 步：逐只股票跑，分练习段/考试段统计 ==========
rows = []
for ticker, name in STOCKS.items():
    df = backtest(ticker)
    if df is None:
        print(f"{name} ({ticker}) 下载失败，跳过")
        continue
    for period, part in [("练习段 2018-22", df[df.index < SPLIT]),
                         ("考试段 2023-今", df[df.index >= SPLIT])]:
        bh = metrics(part["return"])
        st = metrics(part["strategy_return"])
        if not bh:
            continue
        rows.append({
            "股票": name, "阶段": period,
            "持有_年化": bh["年化"], "策略_年化": st["年化"],
            "持有_夏普": bh["夏普"], "策略_夏普": st["夏普"],
            "持有_回撤": bh["最大回撤"], "策略_回撤": st["最大回撤"],
            "策略更好?": "是" if st["夏普"] > bh["夏普"] else "否",
        })

result = pd.DataFrame(rows)

# ========== 第 5 步：打印结果 ==========
pd.set_option("display.unicode.east_asian_width", True)
pd.set_option("display.width", 200)
show = result.copy()
for c in ["持有_年化", "策略_年化", "持有_回撤", "策略_回撤"]:
    show[c] = show[c].map("{:.1%}".format)
for c in ["持有_夏普", "策略_夏普"]:
    show[c] = show[c].map("{:.2f}".format)
print(show.to_string(index=False))

print("\n===== 总结：策略夏普比率 > 一直持有 的股票数量 =====")
for period, g in result.groupby("阶段"):
    win = (g["策略更好?"] == "是").sum()
    print(f"{period}：{win} / {len(g)} 只")

result.to_csv("multi_backtest_result.csv", index=False, encoding="utf-8-sig")
print("\n详细结果已保存到 multi_backtest_result.csv（可用 Excel 打开）")

# ========== 第 6 步：画图：考试段，每只股票两种做法的夏普比率 ==========
plt.rcParams["font.sans-serif"] = ["PingFang SC", "Arial Unicode MS", "SimHei"]  # 让图里能显示中文
plt.rcParams["axes.unicode_minus"] = False

test = result[result["阶段"] == "考试段 2023-今"].set_index("股票")
ax = test[["持有_夏普", "策略_夏普"]].plot(kind="bar", figsize=(11, 5), rot=0)
ax.axhline(0, color="black", linewidth=0.8, label="_nolegend_")   # 0 线不进图例
ax.set_title("考试段（2023-至今）夏普比率：一直持有 vs 均线策略")
ax.set_ylabel("夏普比率（越高越好）")
ax.legend(["一直持有", "均线策略"])
plt.tight_layout()
plt.savefig("multi_backtest_result.png", dpi=150)
plt.show()
