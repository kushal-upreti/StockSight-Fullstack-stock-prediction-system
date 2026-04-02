from django.urls import path
from .views import StockPredictionAPIView, TickerInfoAPIView
urlpatterns= [
    path('predict/', StockPredictionAPIView.as_view(), name='stock_prediction'),
    path('ticker-info/', TickerInfoAPIView.as_view(), name='ticker-info'),
]