from django.contrib import admin

from .models import Transaction, TransactionCategory, TransactionAuditLog

admin.site.register([Transaction, TransactionCategory, TransactionAuditLog])