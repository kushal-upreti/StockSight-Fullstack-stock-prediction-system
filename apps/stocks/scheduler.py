from datetime import timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command
from django.db.models import Max
from django.utils import timezone

import logging

logger = logging.getLogger(__name__)


def refresh_stock_data():
    logger.info("Running scheduled stock data refresh...")
    call_command("fetch_stock_data")


def refresh_if_stale():
    """Startup safety net: refresh if the newest trade_date isn't the most recent completed session."""
    from apps.stocks.models import StockData
    from apps.stocks.management.commands.fetch_stock_data import get_last_completed_trading_date

    expected_date = get_last_completed_trading_date()
    latest_trade_date = StockData.objects.aggregate(latest=Max("trade_date"))["latest"]

    if latest_trade_date is None or latest_trade_date < expected_date:
        logger.info(
            "Stock data outdated (have %s, expected %s) — refreshing now.",
            latest_trade_date, expected_date,
        )
        refresh_stock_data()
    else:
        logger.info("Stock data is current (trade_date=%s) — skipping startup refresh.", latest_trade_date)

def start_scheduler():
    scheduler = BackgroundScheduler(timezone="Asia/Kathmandu")
    scheduler.add_job(
        refresh_stock_data,
        trigger="cron",
        hour=1,
        minute=45,
        id="stock_refresh_job",
        replace_existing=True,
    )
    scheduler.start()
    print("✅ Stock data scheduler started — jobs:", scheduler.get_jobs())  # temporary, remove later
    logger.info("Stock data scheduler started — will refresh daily at 1:45 AM.")

    refresh_if_stale()