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

class DashboardMetricsSerializer(serializers.Serializer):
    """
    Serializer for the main dashboard KPI cards. This is not a ModelSerializer
    as it aggregates data from multiple sources.
    """
    daily_active_users = serializers.IntegerField()
    dau_percentage_change = serializers.FloatField()
    monthly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    revenue_percentage_change = serializers.FloatField()
    active_subscriptions = serializers.IntegerField()
    subscriptions_percentage_change = serializers.FloatField()

class UserGrowthSerializer(serializers.Serializer):
    """
    Serializer for a single data point in the user growth chart.
    """
    period = serializers.DateField()
    new_users = serializers.IntegerField()
    total_users = serializers.IntegerField()

class PackageDistributionSerializer(serializers.Serializer):
    """
    Serializer for package distribution data.
    """
    package__name = serializers.CharField()
    count = serializers.IntegerField()

class UserDemographicsSerializer(serializers.Serializer):
    """
    Serializer for demographics data (e.g., by age, gender).
    """
    group = serializers.CharField()
    count = serializers.IntegerField()