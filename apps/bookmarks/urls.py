from django.urls import path
from .views import BookmarkListView, BookmarkDetailView

urlpatterns = [
    path('', BookmarkListView.as_view(), name='bookmark-list'),
    path('<int:pk>/', BookmarkDetailView.as_view(), name='bookmark-detail'),
]