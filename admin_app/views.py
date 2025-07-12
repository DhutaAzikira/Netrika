from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Case, When, Value, CharField
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.core.cache import cache
from django.contrib.auth.models import User
from dateutil.relativedelta import relativedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser

from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Packages, Transactions, Subscriptions, SystemSetting, UserProfiles
from .serializers import (
    PackageSerializer, TransactionSerializer, SubscriptionSerializer,
    DashboardMetricsSerializer, UserGrowthSerializer, PackageDistributionSerializer,
    UserDemographicsSerializer
)


@extend_schema(tags=["Admin: Package Management"])
class PackageViewSet(ModelViewSet):
    """
    A ViewSet for creating, viewing, and editing packages.
    Only accessible by admin users.
    """
    permission_classes = [IsAdminUser]
    queryset = Packages.objects.all().order_by('price')
    serializer_class = PackageSerializer


@extend_schema(tags=["Admin: Transactions"])
class TransactionViewSet(ModelViewSet):
    """
    A ViewSet for viewing transactions. This is a read-only endpoint.
    """
    permission_classes = [IsAdminUser]
    queryset = Transactions.objects.select_related('user_profile', 'package').all()
    serializer_class = TransactionSerializer
    filterset_fields = ['status', 'user_profile__email', 'package__name']
    http_method_names = ['get', 'head', 'options'] # Read-only


@extend_schema(tags=["Admin: Subscriptions"])
class SubscriptionViewSet(ModelViewSet):
    """
    A ViewSet for viewing and editing user subscriptions.
    """
    permission_classes = [IsAdminUser]
    queryset = Subscriptions.objects.select_related('user_profile', 'package').all()
    serializer_class = SubscriptionSerializer
    filterset_fields = ['is_active', 'user_profile__email', 'package__name']


@extend_schema(tags=["Admin: System Settings"])
class SystemSettingsAPIView(APIView):
    """
    API for managing global system settings.
    """
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Retrieve all system settings",
        description="Returns a key-value dictionary of all current system settings.",
        responses={
            200: inline_serializer(
                name='SystemSettingsGetResponse',
                fields={
                    "ai_coach_enabled": serializers.BooleanField(),
                    "failed_login_attempts_lockout": serializers.IntegerField(),
                    "free_tier_sessions_per_month": serializers.IntegerField(),
                    "login_method_email_password_enabled": serializers.BooleanField(),
                    "login_method_google_oauth_enabled": serializers.BooleanField(),
                    "login_method_linkedin_oauth_enabled": serializers.BooleanField(),
                    "maintenance_mode": serializers.BooleanField(),
                    "max_active_sessions": serializers.IntegerField(),
                    "max_session_duration_minutes": serializers.IntegerField(),
                    "password_expires_after_days": serializers.IntegerField(),
                    "password_expiry_warning_days": serializers.IntegerField(),
                    "password_min_length": serializers.IntegerField(),
                    "password_require_number": serializers.BooleanField(),
                    "password_require_special_char": serializers.BooleanField(),
                    "password_require_uppercase": serializers.BooleanField(),
                    "platform_name": serializers.CharField(),
                    "platform_url": serializers.URLField(),
                    "premium_sessions_per_month": serializers.IntegerField(),
                    "remember_me_duration_days": serializers.IntegerField(),
                    "session_timeout_minutes": serializers.IntegerField(),
                    "support_email": serializers.EmailField(),
                    "timezone": serializers.CharField(),
                    "user_registration_enabled": serializers.BooleanField(),
                    "video_recording_enabled": serializers.BooleanField()
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        settings_qs = SystemSetting.objects.all()
        settings_dict = {setting.key: setting.value for setting in settings_qs}
        return Response(settings_dict)

    @extend_schema(
        summary="Update system settings",
        description="Updates one or more system settings and returns the complete, updated set of all settings.",
        request=inline_serializer(
            name='SystemSettingsPutRequest',
            fields={'some_key': serializers.CharField(default='new_value')}
        ),
        responses={200: inline_serializer(
            name='SystemSettingsPutResponse',
            fields={
                "ai_coach_enabled": serializers.BooleanField(),
                "failed_login_attempts_lockout": serializers.IntegerField(),
                "free_tier_sessions_per_month": serializers.IntegerField(),
                "login_method_email_password_enabled": serializers.BooleanField(),
                "login_method_google_oauth_enabled": serializers.BooleanField(),
                "login_method_linkedin_oauth_enabled": serializers.BooleanField(),
                "maintenance_mode": serializers.BooleanField(),
                "max_active_sessions": serializers.IntegerField(),
                "max_session_duration_minutes": serializers.IntegerField(),
                "password_expires_after_days": serializers.IntegerField(),
                "password_expiry_warning_days": serializers.IntegerField(),
                "password_min_length": serializers.IntegerField(),
                "password_require_number": serializers.BooleanField(),
                "password_require_special_char": serializers.BooleanField(),
                "password_require_uppercase": serializers.BooleanField(),
                "platform_name": serializers.CharField(),
                "platform_url": serializers.URLField(),
                "premium_sessions_per_month": serializers.IntegerField(),
                "remember_me_duration_days": serializers.IntegerField(),
                "session_timeout_minutes": serializers.IntegerField(),
                "support_email": serializers.EmailField(),
                "timezone": serializers.CharField(),
                "user_registration_enabled": serializers.BooleanField(),
                "video_recording_enabled": serializers.BooleanField()
            }
        )}
    )
    def put(self, request, *args, **kwargs):
        for key, value in request.data.items():
            SystemSetting.objects.update_or_create(
                key=key,
                defaults={'value': value}
            )
            cache.delete(f'setting_{key}')

        settings_qs = SystemSetting.objects.all()
        settings_dict = {setting.key: setting.value for setting in settings_qs}

        return Response(settings_dict, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Admin: Dashboard"],
    summary="Get Core Dashboard Metrics",
    description="Provides key performance indicators like DAU, monthly revenue, and active subscriptions with percentage changes.",
    responses={200: DashboardMetricsSerializer}
)
class DashboardMetricsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        start_of_this_month = today.replace(day=1)
        start_of_last_month = (start_of_this_month - timedelta(days=1)).replace(day=1)

        dau_today = User.objects.filter(last_login__date=today).count()
        dau_yesterday = User.objects.filter(last_login__date=yesterday).count()
        dau_change = ((dau_today - dau_yesterday) / dau_yesterday * 100) if dau_yesterday > 0 else 0

        revenue_this_month = Transactions.objects.filter(
            status='Success', created_at__gte=start_of_this_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        revenue_last_month = Transactions.objects.filter(
            status='Success', created_at__gte=start_of_last_month, created_at__lt=start_of_this_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        revenue_change = ((revenue_this_month - revenue_last_month) / revenue_last_month * 100) if revenue_last_month > 0 else 0

        active_subs_count = Subscriptions.objects.filter(is_active=True).count()
        subs_at_start_of_month = Subscriptions.objects.filter(
            start_date__lt=start_of_this_month, is_active=True
        ).count()
        subscriptions_change = ((active_subs_count - subs_at_start_of_month) / subs_at_start_of_month * 100) if subs_at_start_of_month > 0 else 0

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


@extend_schema(
    tags=["Admin: Dashboard"],
    summary="Get User Growth Data",
    description="Provides time-series data for new and total user growth. Can be filtered by a time period.",
    parameters=[
        OpenApiParameter(name='period', type=OpenApiTypes.STR, enum=['daily', 'weekly', 'monthly'], default='monthly',
                         description='The time period to group the growth data by.')
    ],
    responses={200: UserGrowthSerializer(many=True)}
)
class UserGrowthAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        period = request.query_params.get('period', 'monthly').lower()
        if period == 'weekly':
            trunc_level = TruncWeek
        elif period == 'daily':
            trunc_level = TruncDay
        else:
            trunc_level = TruncMonth

        new_user_data = User.objects.annotate(period=trunc_level('date_joined')).values('period').annotate(
            new_users=Count('id')).order_by('period')
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


@extend_schema(
    tags=["Admin: Dashboard"],
    summary="Get Package Subscription Distribution",
    description="Returns the count of active subscribers for each package, showing which packages are most popular.",
    responses={200: PackageDistributionSerializer(many=True)}
)
class PackageDistributionAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        distribution_data = Subscriptions.objects.filter(is_active=True) \
            .values('package__name') \
            .annotate(count=Count('id')) \
            .order_by('-count')
        serializer = PackageDistributionSerializer(instance=distribution_data, many=True)
        return Response(serializer.data)


@extend_schema(
    tags=["Admin: Dashboard"],
    summary="Get User Demographics",
    description="Provides a breakdown of user demographics, which can be grouped by different attributes.",
    parameters=[
        OpenApiParameter(name='group_by', type=OpenApiTypes.STR, enum=['gender', 'age'], default='gender',
                         description='The attribute to group user demographics by.')
    ],
    responses={
        200: UserDemographicsSerializer(many=True),
        400: OpenApiResponse(description="Invalid 'group_by' parameter provided.")
    }
)
class UserDemographicsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        group_by = request.query_params.get('group_by', 'gender').lower()
        if group_by == 'gender':
            queryset = UserProfiles.objects.values('sex') \
                .annotate(group=Value('sex'), count=Count('id')) \
                .values('group', 'count')
        elif group_by == 'age':
            today = timezone.now().date()
            queryset = UserProfiles.objects.annotate(
                age_group=Case(
                    When(date_of_birth__gte=today - relativedelta(years=24), then=Value('18-24')),
                    When(date_of_birth__gte=today - relativedelta(years=34), then=Value('25-34')),
                    When(date_of_birth__gte=today - relativedelta(years=44), then=Value('35-44')),
                    When(date_of_birth__gte=today - relativedelta(years=54), then=Value('45-54')),
                    default=Value('55+'),
                    output_field=CharField()
                )
            ).values('age_group').annotate(group=Value('age_group'), count=Count('id')).values('group', 'count')
        else:
            return Response({"error": "Invalid group_by parameter"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserDemographicsSerializer(instance=queryset, many=True)
        return Response(serializer.data)