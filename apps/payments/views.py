import uuid
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import KhaltiPayment


PLAN_NAME = 'StockSight Pro'


def khalti_url(path):
    return urljoin(settings.KHALTI_BASE_URL.rstrip('/') + '/', path.lstrip('/'))


def khalti_headers():
    return {
        'Authorization': f'Key {settings.KHALTI_SECRET_KEY}',
        'Content-Type': 'application/json',
    }


class KhaltiInitiateView(APIView):
    def post(self, request):
        if not settings.KHALTI_SECRET_KEY:
            return Response(
                {'error': 'KHALTI_SECRET_KEY is not configured.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        frontend_url = settings.FRONTEND_URL.rstrip('/')
        purchase_order_id = f"stocksight-pro-{request.user.id}-{uuid.uuid4().hex[:12]}"
        amount = settings.STOCKSIGHT_PRO_AMOUNT_PAISA

        payload = {
            'return_url': f'{frontend_url}/payment/khalti/return',
            'website_url': frontend_url,
            'amount': amount,
            'purchase_order_id': purchase_order_id,
            'purchase_order_name': PLAN_NAME,
            'customer_info': {
                'name': request.user.full_name or request.user.username,
                'email': request.user.email,
            },
        }

        try:
            khalti_response = requests.post(
                khalti_url('/epayment/initiate/'),
                json=payload,
                headers=khalti_headers(),
                timeout=20,
            )
            khalti_data = khalti_response.json()
        except requests.RequestException as exc:
            return Response(
                {'error': 'Could not initiate Khalti payment.', 'detail': str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except ValueError:
            return Response(
                {'error': 'Khalti returned an invalid response.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if khalti_response.status_code >= 400:
            return Response(
                {'error': 'Khalti payment initiation failed.', 'detail': khalti_data},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pidx = khalti_data.get('pidx')
        payment_url = khalti_data.get('payment_url')
        if not pidx or not payment_url:
            return Response(
                {'error': 'Khalti response did not include payment_url and pidx.', 'detail': khalti_data},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        KhaltiPayment.objects.create(
            user=request.user,
            pidx=pidx,
            purchase_order_id=purchase_order_id,
            amount=amount,
            payment_url=payment_url,
            raw_initiate_response=khalti_data,
        )

        return Response(
            {
                'payment_url': payment_url,
                'pidx': pidx,
                'purchase_order_id': purchase_order_id,
            },
            status=status.HTTP_200_OK,
        )


class KhaltiVerifyView(APIView):
    def post(self, request):
        if not settings.KHALTI_SECRET_KEY:
            return Response(
                {'error': 'KHALTI_SECRET_KEY is not configured.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        pidx = request.data.get('pidx')
        if not pidx:
            return Response({'error': 'pidx is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = KhaltiPayment.objects.get(pidx=pidx, user=request.user)
        except KhaltiPayment.DoesNotExist:
            return Response({'error': 'Payment record not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            khalti_response = requests.post(
                khalti_url('/epayment/lookup/'),
                json={'pidx': pidx},
                headers=khalti_headers(),
                timeout=20,
            )
            khalti_data = khalti_response.json()
        except requests.RequestException as exc:
            return Response(
                {'error': 'Could not verify Khalti payment.', 'detail': str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except ValueError:
            return Response(
                {'error': 'Khalti returned an invalid response.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if khalti_response.status_code >= 400:
            return Response(
                {'error': 'Khalti payment verification failed.', 'detail': khalti_data},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lookup_status = khalti_data.get('status', '')
        transaction_id = khalti_data.get('transaction_id') or ''
        total_amount = khalti_data.get('total_amount')
        try:
            verified_amount = int(total_amount)
        except (TypeError, ValueError):
            verified_amount = None

        with transaction.atomic():
            payment.status = lookup_status or payment.status
            payment.transaction_id = transaction_id
            payment.raw_lookup_response = khalti_data
            payment.save(update_fields=['status', 'transaction_id', 'raw_lookup_response', 'updated_at'])

            if lookup_status == KhaltiPayment.STATUS_COMPLETED:
                if verified_amount != payment.amount:
                    return Response(
                        {
                            'error': 'Verified payment amount does not match the subscription amount.',
                            'status': lookup_status,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                request.user.subscription_status = 'active'
                request.user.subscription_plan = PLAN_NAME
                request.user.save(update_fields=['subscription_status', 'subscription_plan'])

        return Response(
            {
                'status': lookup_status,
                'plan': request.user.subscription_plan,
                'subscription_status': request.user.subscription_status,
                'transaction_id': transaction_id,
            },
            status=status.HTTP_200_OK,
        )


class SubscriptionStatusView(APIView):
    def get(self, request):
        is_subscribed = (
            request.user.subscription_status == 'active'
            and request.user.subscription_plan == PLAN_NAME
        )

        return Response(
            {
                'subscribed': is_subscribed,
                'plan': request.user.subscription_plan,
                'subscription_status': request.user.subscription_status,
                'subscription_plan': request.user.subscription_plan,
            },
            status=status.HTTP_200_OK,
        )
