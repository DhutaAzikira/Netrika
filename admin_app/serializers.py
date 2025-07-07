from rest_framework import serializers
from .models import Packages, Subscriptions, Transactions, SystemSetting


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Packages
        fields = ['id', 'name', 'price', 'features', 'is_active']


class SubscriptionSerializer(serializers.ModelSerializer):
    user_full_name = serializers.CharField(source='user_profile.full_name', read_only=True)
    package_name = serializers.CharField(source='package.name', read_only=True)

    class Meta:
        model = Subscriptions
        fields = [
            'id',
            'user_profile',
            'user_full_name',
            'package',
            'package_name',
            'start_date',
            'end_date',
            'is_active'
        ]
        extra_kwargs = {
            'user_profile': {'write_only': True},
            'package': {'write_only': True}
        }


class TransactionSerializer(serializers.ModelSerializer):
    user_full_name = serializers.CharField(source='user_profile.full_name', read_only=True, allow_null=True)
    package_name = serializers.CharField(source='package.name', read_only=True, allow_null=True)

    class Meta:
        model = Transactions
        fields = [
            'id',
            'transaction_id',
            'user_full_name',
            'package_name',
            'amount',
            'status',
            'created_at'
        ]


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = ['key', 'value']