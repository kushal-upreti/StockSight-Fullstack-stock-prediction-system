from django.contrib import admin
from .models import StockData


@admin.register(StockData)
class StockDataAdmin(admin.ModelAdmin):
    list_display = ["ticker", "name", "sector", "close", "change", "volume", "trade_date", "fetched_at"]
    list_filter = ["sector", "trade_date"]
    search_fields = ["ticker", "name"]
    ordering = ["ticker"]