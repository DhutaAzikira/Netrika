from django.db import models
# Assuming your UserProfiles model is in an app named 'platform_app'
# based on your SQL file's content_type table.
from platform_app.models import UserProfiles

class Packages(models.Model):
    name = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    features = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'packages'
        verbose_name = 'Package'
        verbose_name_plural = 'Packages'

    def __str__(self):
        return self.name

class Subscriptions(models.Model):
    user_profile = models.ForeignKey(UserProfiles, on_delete=models.CASCADE, related_name='subscriptions')
    package = models.ForeignKey(Packages, on_delete=models.PROTECT)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'subscriptions'
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'

    def __str__(self):
        return f"{self.user_profile.full_name}'s {self.package.name} Subscription"

class Transactions(models.Model):
    class Status(models.TextChoices):
        SUCCESS = 'Success', 'Success'
        FAILED = 'Failed', 'Failed'
        PENDING = 'Pending', 'Pending'

    user_profile = models.ForeignKey(UserProfiles, on_delete=models.SET_NULL, null=True, blank=True)
    package = models.ForeignKey(Packages, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status, default=Status.PENDING)
    transaction_id = models.CharField(max_length=100, unique=True, help_text="ID from the payment provider")
    created_at = models.DateTimeField(auto_now_add=True)
    provider_response = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.status}"

class SystemSetting(models.Model):
    key = models.CharField(max_length=100, primary_key=True)
    value = models.JSONField()

    class Meta:
        db_table = 'system_settings'
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'

    def __str__(self):
        return self.key