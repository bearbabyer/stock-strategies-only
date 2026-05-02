"""
抓取台股全部上市/上櫃股票代碼，更新 Google Sheet Watchlist
執行: python -m uv run python fetch_all_stocks.py
"""
import os
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import requests
import gspread
from stock_strategies.sheet import get_gsheet

FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"


def fetch_stock_info() -> list[dict]:
    """從 FinMind 抓台股全部股票基本資料"""
    token = os.environ["FINMIND_TOKEN"]

    all_stocks = []

    for dataset in ["TaiwanStockInfo"]:
        params = {
            "dataset": dataset,
            "token": token,
        }
        print(f"抓取 {dataset}...")
        r = requests.get(FINMIND_URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json().get("data", [])
        print(f"  → 取得 {len(data)} 筆")
        all_stocks.extend(data)

    return all_stocks


def filter_stocks(stocks: list[dict]) -> list[tuple]:
    """
    過濾條件：
    - 只留上市(twse)、上櫃(tpex)
    - 股票代碼為純 4 碼數字（排除 ETF 0開頭、特別股、權證等）
    - 排除名稱含 ETF、DR、受益憑證
    """
    result = []
    seen = set()

    for s in stocks:
        sid = str(s.get("stock_id", "")).strip()
        name = str(s.get("stock_name", "")).strip()
        stype = str(s.get("type", "")).strip()

        if sid in seen:
            continue

        # 只留 4 碼純數字
        if len(sid) != 4 or not sid.isdigit():
            continue

        # 排除 ETF（0開頭）
        if sid.startswith("0"):
            continue

        # 只留上市、上櫃
        if stype not in ("twse", "tpex"):
            continue

        # 排除名稱含特定關鍵字
        if any(x in name for x in ["ETF", "DR", "受益", "基金"]):
            continue

        seen.add(sid)
        result.append((sid, name, stype))

    result.sort(key=lambda x: x[0])
    return result


def update_watchlist(stocks: list[tuple]):
    print(f"\n連線 Google Sheets，寫入 {len(stocks)} 檔...")
    sh = get_gsheet()

    try:
        ws = sh.worksheet("Watchlist")
        ws.clear()
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title="Watchlist", rows=2000, cols=5)

    # 標頭
    rows = [["stock_id", "name", "type", "enabled"]]

    # 上市(sii)優先，其次上櫃(otc)，最後興櫃(rotc)
    type_order = {"sii": 0, "otc": 1, "rotc": 2, "": 3}
    stocks_sorted = sorted(stocks, key=lambda x: (type_order.get(x[2], 3), x[0]))

    for sid, name, stype in stocks_sorted:
        rows.append([sid, name, stype, "TRUE"])

    # 分批寫入（避免超過 API 限制）
    batch_size = 500
    ws.update(range_name="A1", values=rows[:batch_size])
    for i in range(batch_size, len(rows), batch_size):
        time.sleep(1)
        ws.append_rows(rows[i:i+batch_size])
        print(f"  已寫入 {min(i+batch_size, len(rows))}/{len(rows)} 筆")

    print(f"Watchlist 更新完成：{len(stocks)} 檔")


def main():
    raw = fetch_stock_info()
    stocks = filter_stocks(raw)

    type_counts = {}
    for _, _, t in stocks:
        type_counts[t] = type_counts.get(t, 0) + 1

    print(f"\n篩選結果：")
    print(f"  上市 (twse): {type_counts.get('twse', 0)} 檔")
    print(f"  上櫃 (tpex): {type_counts.get('tpex', 0)} 檔")
    print(f"  合計: {len(stocks)} 檔")

    update_watchlist(stocks)
    print("\n完成！可執行 main.py 開始掃描")


if __name__ == "__main__":
    main()
