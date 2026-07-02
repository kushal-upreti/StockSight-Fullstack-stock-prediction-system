from django.conf import settings
from django.db import models


class KhaltiPayment(models.Model):
    STATUS_INITIATED = 'Initiated'
    STATUS_COMPLETED = 'Completed'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='khalti_payments')
    pidx = models.CharField(max_length=100, unique=True, blank=True)
    purchase_order_id = models.CharField(max_length=100, unique=True)
    purchase_order_name = models.CharField(max_length=100, default='StockSight Pro')
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=30, default=STATUS_INITIATED)
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_url = models.URLField(blank=True, max_length=500)
    raw_initiate_response = models.JSONField(default=dict, blank=True)
    raw_lookup_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.purchase_order_id} - {self.status}"
