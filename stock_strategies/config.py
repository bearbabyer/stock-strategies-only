FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"
TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

CONFIG = {
    "eps_threshold": 5.0,
    "roe_threshold": 15.0,
    "backtest_years": 3,
    "hold_days": 20,
    "target_return": 0.10,
    "stop_loss": 0.08,
    "min_tech_score_for_signal": 60,
    "min_total_score_for_buy": 65,
    # 每日輪替掃描：把 Watchlist 分成 N 組，每天掃一組
    # 5 組 × 每組 ~420 檔 × 0.5s ≈ 35 分鐘，週一到週五剛好輪完一輪
    "batch_groups": 5,
    "api_delay": 0.5,
}
