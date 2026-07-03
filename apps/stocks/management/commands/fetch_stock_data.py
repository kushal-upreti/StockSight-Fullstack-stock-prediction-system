# stocks/management/commands/fetch_stock_data.py
import datetime
import yfinance as yf
from django.core.management.base import BaseCommand
from zoneinfo import ZoneInfo  # built-in, no extra dependency needed
from apps.stocks.models import StockData

TICKERS = [
    "AAPL", "MSFT", "GOOGL", "NVDA", "META", "AMD", "TSLA", "AMZN",
    "JPM", "GS", "BAC", "WFC",
    "JNJ", "PFE", "UNH", "ABBV",
    "KO", "PG", "WMT", "MCD",
    "XOM", "CVX", "BA", "CAT",
]

US_EASTERN = ZoneInfo("America/New_York")


def get_last_completed_trading_date():
    """
    Returns the most recent US trading date whose session has definitely
    closed, based on actual close time (4:00 PM ET) rather than a raw
    date comparison — so 'today' in US time only counts once its market
    has actually closed (+ buffer for settlement).
    """
    now_et = datetime.datetime.now(US_EASTERN)
    market_close_today = now_et.replace(hour=16, minute=30, second=0, microsecond=0)  # 15-min settlement buffer
    if now_et < market_close_today:
        # Market hasn't closed yet today (ET) — most recent COMPLETE session is not today.
        return (now_et - datetime.timedelta(days=1)).date()
    return now_et.date()


class Command(BaseCommand):
    help = "Deletes old stock data and fetches the most recent completed trading day's data"

    def handle(self, *args, **options):
        cutoff_date = get_last_completed_trading_date()
        self.stdout.write(f"Cutoff date (last completed session, ET): {cutoff_date}")

        deleted_count, _ = StockData.objects.all().delete()
        self.stdout.write(f"Deleted {deleted_count} old stock records.")

        new_records = []
        for ticker in TICKERS:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="5d")
                if hist.empty:
                    continue

                # Keep only sessions up to and including the cutoff date
                # (i.e. sessions that have definitely closed by now).
                hist = hist[hist.index.date <= cutoff_date]
                if hist.empty:
                    continue

                row = hist.iloc[-1]
                trade_date = hist.index[-1].date()
                prev_close = hist.iloc[-2]["Close"] if len(hist) > 1 else row["Open"]
                change_pct = ((row["Close"] - prev_close) / prev_close) * 100 if prev_close else 0

                info = stock.info
                new_records.append(StockData(
                    ticker=ticker,
                    name=info.get("longName", ticker),
                    sector=info.get("sector", ""),
                    exchange=info.get("exchange", ""),
                    open=round(row["Open"], 2),
                    high=round(row["High"], 2),
                    low=round(row["Low"], 2),
                    close=round(row["Close"], 2),
                    volume=int(row["Volume"]),
                    change=round(change_pct, 2),
                    trade_date=trade_date,
                ))
            except Exception as e:
                self.stderr.write(f"Failed for {ticker}: {e}")

        StockData.objects.bulk_create(new_records)
        self.stdout.write(self.style.SUCCESS(f"Saved {len(new_records)} new stock records."))