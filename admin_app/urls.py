from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import PackageViewSet, TransactionViewSet, SubscriptionViewSet, SystemSettingsAPIView, \
    DashboardMetricsAPIView, UserGrowthAPIView, PackageDistributionAPIView, UserDemographicsAPIView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'packages', PackageViewSet, basename='package')
router.register(r'transactions', TransactionViewSet, basename='transaction') # Add this line
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')



# The API URLs are now determined automatically by the router.
urlpatterns = router.urls + [
    path('settings/', SystemSettingsAPIView.as_view(), name='system-settings'),
    path('dashboard/metrics/', DashboardMetricsAPIView.as_view(), name='dashboard-metrics'),
    path('dashboard/user-growth/', UserGrowthAPIView.as_view(), name='dashboard-user-growth'),
    path('dashboard/package-distribution/', PackageDistributionAPIView.as_view(),name='dashboard-package-distribution'),
    path('dashboard/user-demographics/', UserDemographicsAPIView.as_view(), name='dashboard-user-demographics'),

]


