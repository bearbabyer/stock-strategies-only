"""
V3.0 每日選股訊號系統

執行: uv run python main.py
"""

import os
import sys
import time
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import pytz

from stock_strategies.sheet import read_watchlist, append_signals, already_ran_today
from stock_strategies.evaluate import evaluate
from stock_strategies.notify import send_telegram, format_messages
from stock_strategies.config import CONFIG

TW = pytz.timezone("Asia/Taipei")

REQUIRED_ENV = [
    "FINMIND_TOKEN",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "GOOGLE_SHEET_ID",
    "GOOGLE_CREDS_JSON",
]


def main():
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"缺少環境變數: {missing}", file=sys.stderr)
        sys.exit(1)

    now_tw = datetime.now(TW)
    today = now_tw.strftime("%Y-%m-%d")
    print(f"[台灣時間 {now_tw.strftime('%Y-%m-%d %H:%M')}] 啟動")

    # 台灣時間 14:00 前不執行（確保收盤後才跑）
    if now_tw.hour < 14:
        print(f"  → 台灣時間 {now_tw.strftime('%H:%M')}，未到 14:00，跳過")
        sys.exit(0)

    # 今天已跑過就跳過（防止多個 cron 重複執行）
    if already_ran_today(today):
        print(f"  → {today} 已執行過，跳過")
        sys.exit(0)

    print(f"[{now_tw.strftime('%H:%M')}] 讀取 watchlist...")
    watchlist = read_watchlist()
    print(f"  → {len(watchlist)} 檔")

    results = []
    for i, row in enumerate(watchlist, 1):
        sid = str(row["stock_id"])
        name = row.get("name", "")
        print(f"[{i}/{len(watchlist)}] {sid} {name}")
        r = evaluate(sid, name)
        if r:
            results.append(r)
        time.sleep(CONFIG.get("api_delay", 0.5))

    order = {"BUY": 0, "WATCH": 1, "SKIP": 2, "ERROR": 3}
    results.sort(key=lambda x: (order.get(x.get("action"), 4), -x.get("signal_score", 0)))

    buy_count = sum(1 for r in results if r["action"] == "BUY")
    watch_count = sum(1 for r in results if r["action"] == "WATCH")
    print(f"\n{buy_count} BUY, {watch_count} WATCH（共掃 {len(watchlist)} 檔）")

    print("寫回 Google Sheet...")
    append_signals(results)

    print("發送 Telegram...")
    for msg in format_messages(results, watchlist):
        send_telegram(msg)
        time.sleep(0.5)

    print("完成")


if __name__ == "__main__":
    main()
