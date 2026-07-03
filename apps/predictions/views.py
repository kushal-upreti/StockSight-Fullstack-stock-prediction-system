import joblib
import numpy as np
import pandas as pd
import yfinance as yf
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .serializers import StockPredictionSerializer
from .stock_models.ml_models import get_model

ARTIFACT_DIR = "apps/predictions/stock_models"

model = get_model()

# Load everything the training script saved, instead of hardcoding values
# here — this way the view always matches whatever was actually trained,
# even if HORIZON/FEATURE_COLS change again later.
scaler = joblib.load(f"{ARTIFACT_DIR}/scaler.pkl")
TICKER_TO_ID = joblib.load(f"{ARTIFACT_DIR}/ticker_to_id.pkl")
FEATURE_COLS = joblib.load(f"{ARTIFACT_DIR}/feature_cols.pkl")
CONFIG = joblib.load(f"{ARTIFACT_DIR}/config.pkl")

SEQ_LEN = CONFIG["seq_len"]
HORIZON = CONFIG["horizon"]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Recompute the same features the model was trained on."""
    df = df.copy()
    c = df["Close"].squeeze()
    df["ret"] = c.pct_change()
    df = df.dropna()
    return df


class StockPredictionAPIView(APIView):
    """
    Predicts whether a ticker's price will be UP or DOWN `HORIZON` trading
    days from now, using the last `SEQ_LEN` days of daily returns.
    """

    def post(self, request):
        serializer = StockPredictionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        ticker = serializer.validated_data["ticker"].upper()

        # A few months of history is enough since the model only looks at
        # the most recent SEQ_LEN daily returns.
        df = yf.download(ticker, period="6mo", auto_adjust=True, progress=False)
        if df.empty:
            return Response(
                {"error": "No data found for the given ticker"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Keep the last 60 trading days of real closing prices for the chart,
        # taken before feature engineering drops the first row to pct_change.
        price_history = [
            {"date": str(idx.date()), "close": round(float(close), 2)}
            for idx, close in df["Close"].tail(60).items()
        ]

        df = build_features(df)

        if len(df) < SEQ_LEN:
            return Response(
                {"error": "Not enough historical data to make a prediction"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        last_seq = df[FEATURE_COLS].values[-SEQ_LEN:]
        scaled_seq = np.clip(scaler.transform(last_seq), -5, 5)
        X = scaled_seq.reshape(1, SEQ_LEN, len(FEATURE_COLS))

        ticker_id = TICKER_TO_ID.get(ticker)
        is_known_ticker = ticker_id is not None
        ticker_ids = np.array([[ticker_id if is_known_ticker else 0]])

        prob_up = float(model.predict([X, ticker_ids], verbose=0)[0, 0])
        direction = "UP" if prob_up >= 0.5 else "DOWN"
        confidence = prob_up if direction == "UP" else 1 - prob_up

        return Response(
            {
                "status": "success",
                "ticker": ticker,
                "direction": direction,
                "probability_up": round(prob_up, 4),
                "confidence": round(confidence, 4),
                "horizon_days": HORIZON,
                "used_known_ticker_embedding": is_known_ticker,
                "price_history": price_history,
                "note": (
                    "This model's validation accuracy is modest (~53% on a "
                    "single split) and has not been backtested with trading "
                    "costs — treat this as a weak signal, not a recommendation."
                ),
            }
        )


class TickerInfoAPIView(APIView):
    def get(self, request):
        ticker = request.query_params.get("ticker")
        if not ticker:
            return Response(
                {"error": "Ticker is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            info = yf.Ticker(ticker).info
            return Response(
                {
                    "Symbol": info.get("symbol", ticker),
                    "Name": info.get("longName", "---"),
                    "Industry": info.get("industry", "---"),
                    "Country": info.get("country", "---"),
                    "Exchange": info.get("exchange", "---"),
                    "Currency": info.get("currency", "---"),
                    "Market Cap": info.get("marketCap", "---"),
                    "Website": info.get("website", "---"),
                    "Description": info.get("longBusinessSummary", "---"),
                }
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )