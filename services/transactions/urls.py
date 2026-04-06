from django.urls import path

from .api import createtransactioncategory, updatetransactioncategory, gettransactioncategories, \
    createtransactionrecord, updatetransactionrecord, gettransactionrecords, gettransactionrecorddetail, \
    deletetransactionrecord

urlpatterns = [
    path('create-transaction-category/', createtransactioncategory, name='create_transaction_category'),
    path('update-transaction-category/', updatetransactioncategory, name='update_transaction_category'),
    path('get-transaction-categories/', gettransactioncategories, name='get_transaction_categories'),

    path('create-transaction-record/', createtransactionrecord, name='create_transaction_record'),
    path('update-transaction-record/', updatetransactionrecord, name='update_transaction_record'),
    path('get-transaction-records/', gettransactionrecords, name='get_transaction_records'),
    path('get-transaction-record-detail/', gettransactionrecorddetail, name='get_transaction_record_detail'),
    path('delete-transaction-record/', deletetransactionrecord, name='delete_transaction_record'),
]