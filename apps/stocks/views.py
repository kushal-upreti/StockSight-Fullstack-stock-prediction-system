from rest_framework import viewsets
from .models import StockData
from rest_framework.permissions import AllowAny
from .serializers import StockDataSerializer
import logging
import yfinance as yf
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class StockDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockData.objects.all()
    serializer_class = StockDataSerializer


logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 60 * 15  # 15 minutes


class StockDetailView(APIView):
    """
    GET /api/stocks/<ticker>/detail/

    Returns everything needed for a stock detail page:
    - key stats (price, market cap, PE, 52w range, etc.)
    - 30-day OHLC history for the line chart
    - recent news headlines related to the ticker
    """

    def get(self, request, ticker):
        ticker = ticker.upper().strip()
        cache_key = f"stock_detail:{ticker}"

        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            if not info or info.get("regularMarketPrice") is None and not info.get("longName"):
                return Response(
                    {"detail": f"No data found for ticker '{ticker}'."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # ── 30-day price history for the line chart ──────────────────
            hist = stock.history(period="1mo")
            history_data = [
                {
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": round(float(row["Open"]), 2) if row["Open"] == row["Open"] else None,
                    "high": round(float(row["High"]), 2) if row["High"] == row["High"] else None,
                    "low": round(float(row["Low"]), 2) if row["Low"] == row["Low"] else None,
                    "close": round(float(row["Close"]), 2) if row["Close"] == row["Close"] else None,
                    "volume": int(row["Volume"]) if row["Volume"] == row["Volume"] else None,
                }
                for idx, row in hist.iterrows()
            ]

            # ── Key stats ──────────────────────────────────────────────
            stats = {
                "ticker": ticker,
                "name": info.get("longName", ticker),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "exchange": info.get("exchange", ""),
                "currency": info.get("currency", "USD"),
                "currentPrice": info.get("currentPrice") or info.get("regularMarketPrice"),
                "previousClose": info.get("previousClose"),
                "open": info.get("open") or info.get("regularMarketOpen"),
                "dayHigh": info.get("dayHigh"),
                "dayLow": info.get("dayLow"),
                "volume": info.get("volume") or info.get("regularMarketVolume"),
                "avgVolume10Day": info.get("averageDailyVolume10Day"),
                "marketCap": info.get("marketCap"),
                "peRatio": info.get("trailingPE"),
                "forwardPE": info.get("forwardPE"),
                "eps": info.get("trailingEps"),
                "dividendYield": info.get("dividendYield"),
                "dividendRate": info.get("dividendRate"),
                "exDividendDate": info.get("exDividendDate"),
                "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
                "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
                "beta": info.get("beta"),
                "sharesOutstanding": info.get("sharesOutstanding"),
                "targetMeanPrice": info.get("targetMeanPrice"),
                "recommendationKey": info.get("recommendationKey"),
                "website": info.get("website"),
                "longBusinessSummary": info.get("longBusinessSummary"),
            }

            # ── News ───────────────────────────────────────────────────
            news_items = []
            try:
                raw_news = stock.news or []
                for item in raw_news[:10]:
                    content = item.get("content", item)  # yfinance news shape varies by version
                    news_items.append({
                        "title": content.get("title"),
                        "publisher": (content.get("provider") or {}).get("displayName")
                                     or item.get("publisher"),
                        "link": (content.get("canonicalUrl") or {}).get("url")
                                or item.get("link"),
                        "publishedAt": content.get("pubDate") or item.get("providerPublishTime"),
                        "thumbnail": (
                            (content.get("thumbnail") or {}).get("resolutions", [{}])[0].get("url")
                            if content.get("thumbnail") else None
                        ),
                    })
            except Exception as e:
                logger.warning("News fetch failed for %s: %s", ticker, e)

            payload = {
                "stats": stats,
                "history": history_data,
                "news": news_items,
            }

            cache.set(cache_key, payload, CACHE_TTL_SECONDS)
            return Response(payload)

        except Exception as e:
            logger.exception("Failed to fetch stock detail for %s", ticker)
            return Response(
                {"detail": f"Failed to fetch data for '{ticker}': {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )