from django.urls import path
from .views import TransactionReportView, TransactionSummaryView, SendNotificationView

urlpatterns = [
    path('api/transaction-report/', TransactionReportView.as_view(), name='transaction-report'),
    path('api/transaction-summary-report/', TransactionSummaryView.as_view(), name='transaction-summary-report'),
    path('send-notification/', SendNotificationView.as_view(), name='send_notification'),
]
