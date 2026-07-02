from django.urls import path

from .views import KhaltiInitiateView, KhaltiVerifyView, SubscriptionStatusView


urlpatterns = [
    path('khalti/initiate/', KhaltiInitiateView.as_view(), name='khalti-initiate'),
    path('khalti/verify/', KhaltiVerifyView.as_view(), name='khalti-verify'),
    path('subscription/status/', SubscriptionStatusView.as_view(), name='subscription-status'),
]
