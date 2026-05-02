"""
一次性腳本：建立 Watchlist 和 Signals 工作表，並填入台股清單
執行: python -m uv run python setup_watchlist.py
"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import gspread
from stock_strategies.sheet import get_gsheet

WATCHLIST = [
    # 半導體
    ("2330", "台積電"),
    ("2303", "聯電"),
    ("2454", "聯發科"),
    ("3034", "聯詠"),
    ("2379", "瑞昱"),
    ("2344", "華邦電"),
    ("3661", "世芯-KY"),
    ("2408", "南亞科"),
    ("2449", "京元電子"),
    ("6770", "力積電"),
    # 電子/科技
    ("2317", "鴻海"),
    ("2382", "廣達"),
    ("2357", "華碩"),
    ("4938", "和碩"),
    ("2308", "台達電"),
    ("2395", "研華"),
    ("3008", "大立光"),
    ("2327", "國巨"),
    ("2301", "光寶科"),
    ("2353", "宏碁"),
    ("3231", "緯創"),
    ("2356", "英業達"),
    ("3711", "日月光投控"),
    ("2337", "旺宏"),
    ("6415", "矽力-KY"),
    # 金融
    ("2881", "富邦金"),
    ("2882", "國泰金"),
    ("2886", "兆豐金"),
    ("2884", "玉山金"),
    ("2885", "元大金"),
    ("2891", "中信金"),
    ("2892", "第一金"),
    ("5880", "合庫金"),
    # 傳產/石化
    ("6505", "台塑化"),
    ("1301", "台塑"),
    ("1303", "南亞"),
    ("1326", "台化"),
    ("2002", "中鋼"),
    # 通訊/電信
    ("2412", "中華電"),
    ("3045", "台灣大"),
    ("4904", "遠傳"),
    # 生技/醫療
    ("4711", "台灣醫療"),
    ("4739", "康那香"),
    ("6547", "高端疫苗"),
    # 電動車/綠能
    ("3682", "亞太電"),
    ("6452", "康友-KY"),
    ("3533", "嘉澤"),
]

def main():
    print("連線 Google Sheets...")
    sh = get_gsheet()

    # 建立或清空 Watchlist
    try:
        ws = sh.worksheet("Watchlist")
        ws.clear()
        print("已清空現有 Watchlist")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title="Watchlist", rows=200, cols=5)
        print("已建立 Watchlist 工作表")

    # 寫入標頭 + 股票清單
    rows = [["stock_id", "name", "enabled"]]
    rows += [[sid, name, "TRUE"] for sid, name in WATCHLIST]
    ws.update(range_name="A1", values=rows)
    print(f"已寫入 {len(WATCHLIST)} 檔股票")

    # 確保 Signals 工作表存在
    try:
        sh.worksheet("Signals")
        print("Signals 工作表已存在")
    except gspread.WorksheetNotFound:
        sig_ws = sh.add_worksheet(title="Signals", rows=1000, cols=20)
        sig_ws.append_row([
            "date", "stock_id", "name", "action", "signal_score",
            "entry_price", "stop_loss_price", "target_price",
            "rr_ratio", "position_pct", "winrate", "samples",
            "tech_signals", "risk_notes"
        ])
        print("已建立 Signals 工作表")

    print("\n完成！現在可以執行 main.py")

if __name__ == "__main__":
    main()
