from django.db import models

class StockData(models.Model):
    ticker = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=255)
    sector = models.CharField(max_length=100, blank=True)
    exchange = models.CharField(max_length=50, blank=True)

    open = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    high = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    low = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    close = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    volume = models.BigIntegerField(null=True)
    change = models.DecimalField(max_digits=8, decimal_places=2, null=True)

    trade_date = models.DateField()  # the date the OHLC data is FOR (yesterday)
    fetched_at = models.DateTimeField(auto_now_add=True)  # when we pulled it

    class Meta:
        ordering = ["ticker"]
        indexes = [models.Index(fields=["ticker", "trade_date"])]

    def __str__(self):
        return f"{self.ticker} - {self.trade_date}"
