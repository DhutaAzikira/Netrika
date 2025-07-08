from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser

from .models import Packages
from .serializers import PackageSerializer, DashboardMetricsSerializer, PackageDistributionSerializer

# New imports for Transactions
from .models import Transactions
from .serializers import TransactionSerializer

from .models import Subscriptions
from .serializers import SubscriptionSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from django.core.cache import cache

# ... all your previous imports for models and serializers
from .models import SystemSetting
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from django.db.models import Count
from .serializers import UserGrowthSerializer # Add this import

class PackageViewSet(ModelViewSet):
    """
    A ViewSet for creating, viewing, and editing packages.
    Only accessible by admin users.
    """
    queryset = Packages.objects.all().order_by('price')
    serializer_class = PackageSerializer
    permission_classes = [IsAdminUser]


# Add this new ViewSet
class TransactionViewSet(ModelViewSet):
    """
    A ViewSet for viewing transactions.
    """
    # Use select_related to optimize DB queries by pre-fetching related data
    queryset = Transactions.objects.select_related('user_profile', 'package').all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAdminUser]

    # Define which fields can be used for filtering
    filterset_fields = ['status', 'user_profile__email', 'package__name']

    # Make this endpoint read-only (no creating/deleting transactions via API)
    http_method_names = ['get', 'head', 'options']


class SubscriptionViewSet(ModelViewSet):
    """
    A ViewSet for viewing and editing user subscriptions.
    """
    queryset = Subscriptions.objects.select_related('user_profile', 'package').all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAdminUser]

    # Allow filtering by active status, user email, or package name
    filterset_fields = ['is_active', 'user_profile__email', 'package__name']


class SystemSettingsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        settings_qs = SystemSetting.objects.all()
        settings_dict = {setting.key: setting.value for setting in settings_qs}
        return Response(settings_dict)

    def put(self, request, *args, **kwargs):
        for key, value in request.data.items():
            SystemSetting.objects.update_or_create(
                key=key,
                defaults={'value': value}
            )
            # Clear the cache for the updated key
            cache.delete(f'setting_{key}')

        return Response({"message": "Settings updated successfully"}, status=status.HTTP_200_OK)


class DashboardMetricsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        start_of_this_month = today.replace(day=1)
        start_of_last_month = (start_of_this_month - timedelta(days=1)).replace(day=1)

        # 1. Daily Active Users (DAU)
        dau_today = User.objects.filter(last_login__date=today).count()
        dau_yesterday = User.objects.filter(last_login__date=yesterday).count()
        dau_change = ((dau_today - dau_yesterday) / dau_yesterday * 100) if dau_yesterday > 0 else 0

        # 2. Monthly Revenue
        revenue_this_month = Transactions.objects.filter(
            status='Success', created_at__gte=start_of_this_month
        ).aggregate(total=Sum('amount'))['total'] or 0

        revenue_last_month = Transactions.objects.filter(
            status='Success', created_at__gte=start_of_last_month, created_at__lt=start_of_this_month
        ).aggregate(total=Sum('amount'))['total'] or 0

        revenue_change = ((
                                  revenue_this_month - revenue_last_month) / revenue_last_month * 100) if revenue_last_month > 0 else 0

        # 3. Active Subscriptions
        active_subs_count = Subscriptions.objects.filter(is_active=True).count()
        subs_at_start_of_month = Subscriptions.objects.filter(
            start_date__lt=start_of_this_month,
            is_active=True
        ).count()

        subscriptions_change = ((
                                        active_subs_count - subs_at_start_of_month) / subs_at_start_of_month * 100) if subs_at_start_of_month > 0 else 0

        # Prepare data for the serializer
        data = {
            'daily_active_users': dau_today,
            'dau_percentage_change': round(dau_change, 2),
            'monthly_revenue': revenue_this_month,
            'revenue_percentage_change': round(revenue_change, 2),
            'active_subscriptions': active_subs_count,
            'subscriptions_percentage_change': round(subscriptions_change, 2)
        }

        serializer = DashboardMetricsSerializer(instance=data)
        return Response(serializer.data)

class UserGrowthAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        period = request.query_params.get('period', 'monthly').lower()

        # Determine the truncation level based on the period parameter
        if period == 'weekly':
            trunc_level = TruncWeek
        elif period == 'daily':
            trunc_level = TruncDay
        else: # Default to monthly
            trunc_level = TruncMonth

        # Group users by the chosen period and count new users in each period
        new_user_data = User.objects.annotate(period=trunc_level('date_joined')).values('period').annotate(new_users=Count('id')).order_by('period')

        # Calculate the cumulative total users for each period
        chart_data = []
        total_users_so_far = 0
        for item in new_user_data:
            total_users_so_far += item['new_users']
            chart_data.append({
                'period': item['period'],
                'new_users': item['new_users'],
                'total_users': total_users_so_far
            })

        serializer = UserGrowthSerializer(instance=chart_data, many=True)
        return Response(serializer.data)

class PackageDistributionAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        """
        Returns the count of active subscribers for each package.
        """
        distribution_data = Subscriptions.objects.filter(is_active=True)\
            .values('package__name')\
            .annotate(count=Count('id'))\
            .order_by('-count')

        serializer = PackageDistributionSerializer(instance=distribution_data, many=True)
        return Response(serializer.data)


from django.db.models import Case, When, Value
from dateutil.relativedelta import relativedelta
from .models import UserProfiles
from .serializers import UserDemographicsSerializer  # Add this import


# ... existing ViewSets and Views ...


# Add this final APIView for the dashboard
class UserDemographicsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        group_by = request.query_params.get('group_by', 'gender').lower()

        # Group by Gender
        if group_by == 'gender':
            queryset = UserProfiles.objects.values('sex') \
                .annotate(group=Value('sex'), count=Count('id')) \
                .values('group', 'count')

        # Group by Age
        elif group_by == 'age':
            today = timezone.now().date()
            queryset = UserProfiles.objects.annotate(
                age_group=Case(
                    When(date_of_birth__gte=today - relativedelta(years=24), then=Value('18-24')),
                    When(date_of_birth__gte=today - relativedelta(years=34), then=Value('25-34')),
                    When(date_of_birth__gte=today - relativedelta(years=44), then=Value('35-44')),
                    When(date_of_birth__gte=today - relativedelta(years=54), then=Value('45-54')),
                    default=Value('55+'),
                    output_field=models.CharField()
                )
            ).values('age_group').annotate(group=Value('age_group'), count=Count('id')).values('group', 'count')

        else:
            # Default or handle other cases
            return Response({"error": "Invalid group_by parameter"}, status=400)

        serializer = UserDemographicsSerializer(instance=queryset, many=True)
        return Response(serializer.data)