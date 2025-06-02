import yfinance as yf
from datetime import datetime

def compare_index_performance():
    """
    Compares the YTD performance of specified global indices against the S&P 500
    as of May 1, 2025.
    """
    target_date_str = "2025-05-01"
    start_date_str = "2025-01-01"

    # Define the S&P 500 ticker
    sp500_ticker = "^GSPC"

    # Define the list of other global indices and their tickers
    # (The user's image lists 10 other indices)
    other_indices = {
        "中国 - 上证综合指数 (China - Shanghai Composite)": "000001.SS",
        "香港 - 恒生指数 (Hong Kong - Hang Seng Index)": "^HSI",
        "澳大利亚 - S&P/ASX 200 (Australia - S&P/ASX 200)": "^AXJO",
        "印度 - Nifty 50 (India - Nifty 50)": "^NSEI",
        "加拿大 - 标普/多伦多证券交易所综合指数 (Canada - S&P/TSX Composite)": "^GSPTSE",
        "德国 - DAX (Germany - DAX)": "^GDAXI",
        "英国 - 富时 100 指数 (UK - FTSE 100)": "^FTSE",
        "日本 - 日经 225 指数 (Japan - Nikkei 225)": "^N225",
        "墨西哥 - IPC 墨西哥 (Mexico - IPC Mexico)": "^MXX",
        "巴西 - 伊博维斯帕指数 (Brazil - IBOVESPA)": "^BVSP"
    }

    print(f"Data as of: {target_date_str}\n")

    # Fetch S&P 500 YTD performance
    try:
        sp500_data = yf.Ticker(sp500_ticker)
        sp500_hist = sp500_data.history(start=start_date_str, end=target_date_str)
        if sp500_hist.empty or len(sp500_hist) < 2:
            print(f"Could not retrieve sufficient historical data for S&P 500 ({sp500_ticker}).")
            return

        sp500_start_price = sp500_hist['Close'].iloc[0]
        sp500_end_price = sp500_hist['Close'].iloc[-1]
        sp500_ytd_return = ((sp500_end_price - sp500_start_price) / sp500_start_price) * 100
        print(f"美国 - 标准普尔500指数 ({sp500_ticker}) 年初至今回报率 (YTD Return): {sp500_ytd_return:.2f}%")
    except Exception as e:
        print(f"Could not retrieve data for S&P 500 ({sp500_ticker}): {e}")
        return

    print("-" * 70)

    outperforming_indices_count = 0
    results = []

    # Fetch and compare performance for other indices
    for name, ticker in other_indices.items():
        try:
            index_data = yf.Ticker(ticker)
            index_hist = index_data.history(start=start_date_str, end=target_date_str)

            if index_hist.empty or len(index_hist) < 2:
                print(f"Could not retrieve sufficient historical data for {name} ({ticker}).")
                results.append({"name": name, "ticker": ticker, "ytd_return": "N/A", "outperformed_sp500": "N/A"})
                continue

            index_start_price = index_hist['Close'].iloc[0]
            index_end_price = index_hist['Close'].iloc[-1]
            index_ytd_return = ((index_end_price - index_start_price) / index_start_price) * 100
            results.append({"name": name, "ticker": ticker, "ytd_return": f"{index_ytd_return:.2f}%"})

            if index_ytd_return > sp500_ytd_return:
                outperforming_indices_count += 1
                results[-1]["outperformed_sp500"] = True
                print(f"{name} ({ticker}) 年初至今回报率 (YTD Return): {index_ytd_return:.2f}% (Outperformed S&P 500)")
            else:
                results[-1]["outperformed_sp500"] = False
                print(f"{name} ({ticker}) 年初至今回报率 (YTD Return): {index_ytd_return:.2f}%")

        except Exception as e:
            print(f"Could not retrieve data for {name} ({ticker}): {e}")
            results.append({"name": name, "ticker": ticker, "ytd_return": "Error", "outperformed_sp500": "Error"})
        print("-" * 70)

    print("\n======================================================================")
    print(f"总结：截至 {target_date_str}，在 {len(other_indices)} 个全球主要股指中，")
    print(f"有 {outperforming_indices_count} 个指数的年初至今回报率高于美国标准普尔500指数。")
    print("======================================================================\n")

    # Optional: Print a summary table of results
    print("详细结果:")
    print(f"{'Index Name':<55} | {'Ticker':<15} | {'YTD Return':<15} | {'Outperformed S&P 500':<20}")
    print("="*110)
    for res in results:
        status = "Yes" if res.get("outperformed_sp500") is True else ("No" if res.get("outperformed_sp500") is False else res.get("outperformed_sp500", "N/A"))
        print(f"{res['name']:<55} | {res['ticker']:<15} | {res.get('ytd_return', 'N/A'):<15} | {status:<20}")

if __name__ == "__main__":
    # Note: yfinance fetches live or historical data.
    # Since 2025-05-01 is in the future as of my current knowledge cutoff,
    # this code will likely fetch the most recent available data if run today
    # or fail if the dates are too far in the future for yfinance's current data.
    # For actual 2025 data, this script would need to be run on or after 2025-05-01.
    # For demonstration, if you run it now, it will use current data up to today if end_date is in future.
    # To test with past data, change start_date_str and target_date_str to historical dates.

    # Example for testing with historical data (e.g., YTD as of May 1, 2023)
    # To run for 2025 as requested, you'd execute this on or after May 1, 2025.
    # For now, let's assume we want to see how it works, it might pick up latest data or specific historical.
    # To exactly match the prompt for a future date, the market data for that date must exist.

    print("提醒：yfinance 将尝试获取截至指定日期的最新可用数据。\n由于 2025年5月1日 是未来的日期，实际数据将在该日期之后可用。\n现在运行此脚本将获取当前可用的最新数据（如果开始日期和结束日期允许），或者如果日期范围无效，则可能会失败。\n")

    compare_index_performance()