# Moving-Average Crossover Backtest (均线趋势跟踪策略回测)

A small Python project that tests a simple trend-following strategy on China A-share stocks and ETFs, and checks whether the results hold up out of sample.

## Strategy

- Compute the 20-day and 60-day moving averages of the closing price.
- Hold the stock when the 20-day average is above the 60-day average; otherwise stay in cash (long-only).
- Signals are executed on the **next** trading day (`shift(1)`), so the backtest never uses information that was not yet available (no look-ahead bias).
- The benchmark is buy-and-hold.

## Files

| File | What it does |
|---|---|
| `ma_backtest.py` | Version 1: one stock (Sieyuan Electric, 002028.SZ). Prints performance metrics and plots the equity curve. |
| `multi_backtest.py` | Version 2: 8 stocks/ETFs, 0.1% transaction cost per trade, and an in-sample (2018–2022) vs out-of-sample (2023 onwards) split. Saves a results table (CSV) and a bar chart. |

## Metrics

- **Annualised return**: compounded total return converted to a yearly rate (252 trading days per year)
- **Sharpe ratio**: annualised return divided by annualised volatility (risk-free rate taken as 0)
- **Maximum drawdown**: largest peak-to-trough loss

The strategy "beats" buy-and-hold on a stock when its Sharpe ratio is higher.

## Results

| Period | Stocks where the strategy beat buy-and-hold |
|---|---|
| In-sample (2018–2022) | 5 of 8 |
| Out-of-sample (2023 onwards) | 3 of 8 |

**Takeaway:** the strategy helps in trending markets but loses in sideways markets, where prices cross the averages back and forth and each false signal costs money. Good in-sample results did not carry over out of sample.

## Limitations

- Only 8 instruments, chosen from a personal watchlist (selection bias)
- One parameter set (20/60), no parameter sensitivity test
- No slippage, and no modelling of A-share limit-up/limit-down days when trades cannot be filled
- No stop-loss or position sizing

## How to run

```bash
pip install -r requirements.txt
python ma_backtest.py
python multi_backtest.py
```

Price data is downloaded from Yahoo Finance through `yfinance` (adjusted prices).

*This is a learning project, not investment advice.*
