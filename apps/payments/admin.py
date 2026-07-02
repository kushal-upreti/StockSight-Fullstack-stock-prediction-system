from django.contrib import admin

from .models import KhaltiPayment


@admin.register(KhaltiPayment)
class KhaltiPaymentAdmin(admin.ModelAdmin):
    list_display = ['purchase_order_id', 'user', 'amount', 'status', 'transaction_id', 'created_at']
    search_fields = ['purchase_order_id', 'pidx', 'transaction_id', 'user__username', 'user__email']
    list_filter = ['status', 'created_at']
    readonly_fields = ['created_at', 'updated_at', 'raw_initiate_response', 'raw_lookup_response']
