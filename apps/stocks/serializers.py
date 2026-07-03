# stocks/serializers.py
from rest_framework import serializers
from .models import StockData


class StockDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockData
        fields = ["id", "ticker", "name", "sector", "exchange",
                  "open", "high", "low", "close", "volume", "change", "trade_date"]