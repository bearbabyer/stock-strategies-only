"""
V3.0 每日選股訊號系統

執行: uv run python main.py
輪替邏輯: 2119 檔分 5 組，每天（週一~週五）掃一組，一週掃完全部
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

from stock_strategies.sheet import read_watchlist, append_signals
from stock_strategies.evaluate import evaluate
from stock_strategies.notify import send_telegram, format_messages
from stock_strategies.config import CONFIG


REQUIRED_ENV = [
    "FINMIND_TOKEN",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "GOOGLE_SHEET_ID",
    "GOOGLE_CREDS_JSON",
]


def get_today_batch(watchlist: list, groups: int) -> tuple[list, int, int]:
    """依今天是週幾決定掃哪一組（週一=0 … 週五=4）"""
    weekday = datetime.now().weekday()  # 0=Monday, 4=Friday
    group_idx = weekday % groups
    size = len(watchlist)
    chunk = (size + groups - 1) // groups
    start = group_idx * chunk
    end = min(start + chunk, size)
    return watchlist[start:end], group_idx + 1, groups


def main():
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"缺少環境變數: {missing}", file=sys.stderr)
        sys.exit(1)

    print(f"[{datetime.now()}] 讀取 watchlist...")
    watchlist = read_watchlist()
    total = len(watchlist)
    print(f"  → 全部 {total} 檔")

    groups = CONFIG.get("batch_groups", 5)
    batch, group_idx, total_groups = get_today_batch(watchlist, groups)
    print(f"  → 今日掃描第 {group_idx}/{total_groups} 組，共 {len(batch)} 檔")

    results = []
    for i, row in enumerate(batch, 1):
        sid = str(row["stock_id"])
        name = row.get("name", "")
        print(f"[{i}/{len(batch)}] {sid} {name}")
        r = evaluate(sid, name)
        if r:
            results.append(r)
        time.sleep(CONFIG.get("api_delay", 0.5))

    order = {"BUY": 0, "WATCH": 1, "SKIP": 2, "ERROR": 3}
    results.sort(key=lambda x: (order.get(x.get("action"), 4), -x.get("signal_score", 0)))

    buy_count = sum(1 for r in results if r["action"] == "BUY")
    watch_count = sum(1 for r in results if r["action"] == "WATCH")
    print(f"\n{buy_count} BUY, {watch_count} WATCH（本組 {len(batch)} 檔，第 {group_idx}/{total_groups} 組）")

    print("寫回 Google Sheet...")
    append_signals(results)

    print("發送 Telegram...")
    for msg in format_messages(results, batch):
        send_telegram(msg)
        time.sleep(0.5)

    print("完成")


if __name__ == "__main__":
    main()
