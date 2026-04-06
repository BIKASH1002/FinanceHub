
import uuid
from django.db import models
from django.contrib.auth.models import User

from utilities.constants import TRANSACTION_TYPE_CHOICES, TRANSACTION_AUDIT_ACTION_CHOICES


class TransactionCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="transactioncategory_created_by")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="transactioncategory_updated_by")

    class Meta:
        db_table = "transaction_category"
        ordering = ["id"]
        unique_together = ("name", "transaction_type")

    def __str__(self):
        return f"{self.name} - {self.transaction_type}"


class Transaction(models.Model):
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    category = models.ForeignKey(TransactionCategory, on_delete=models.CASCADE, related_name="transactions")
    transaction_date = models.DateField()
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="transaction_created_by")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="transaction_updated_by")

    class Meta:
        db_table = "transaction"
        ordering = ["-transaction_date", "-id"]

    def __str__(self):
        return f"{self.title} - {self.transaction_type} - {self.amount}"


class TransactionAuditLog(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="transaction_audit_logs")
    action = models.CharField(max_length=20, choices=TRANSACTION_AUDIT_ACTION_CHOICES)
    action_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name="transactionauditlog_action_by")
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transaction_audit_log"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.transaction.transaction_id} - {self.action}"