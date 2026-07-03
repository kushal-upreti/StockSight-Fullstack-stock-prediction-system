from django.urls import path
from .views import StockDataViewSet, StockDetailView

stock_list = StockDataViewSet.as_view({"get": "list"})
stock_detail = StockDataViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    path("stocks/", stock_list, name="stock-list"),
    path("stocks/<str:ticker>/detail/", StockDetailView.as_view(), name="stock-detail"),
     ]