from django.urls import path

from .api import getdashboardsummary, getcategorywisesummary, getmonthlytransactiontrend, \
    getrecenttransactionactivity, gettransactionauditlogs

urlpatterns = [
    path('get-dashboard-summary/', getdashboardsummary, name='get_dashboard_summary'),
    path('get-category-wise-summary/', getcategorywisesummary, name='get_category_wise_summary'),
    path('get-monthly-transaction-trend/', getmonthlytransactiontrend, name='get_monthly_transaction_trend'),
    path('get-recent-transaction-activity/', getrecenttransactionactivity, name='get_recent_transaction_activity'),
    path('get-transaction-audit-logs/', gettransactionauditlogs, name='get_transaction_audit_logs'),
]