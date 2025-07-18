from django.http import JsonResponse
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from PlatformInterview import settings
from . import views
from platform_app.views import GoogleLogin, CustomAuthToken
from rest_framework.authtoken.views import obtain_auth_token
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

import yaml, os

def serve_openapi_schema(request):
    yaml_path = os.path.join(settings.BASE_DIR, 'schema.yml')
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    return JsonResponse(data)

urlpatterns = [
    path ('admin/', include('admin_app.urls')),
    path('auth/google/', GoogleLogin.as_view(), name='google_login'),
    path('register/', views.register_api, name='register-api'),
    path('login/', CustomAuthToken.as_view(), name='login-api'),
    path('submit-screener/', views.submit_screener_api, name='submit-screener-api'),
    path('dashboard-data/', views.dashboard_data_api, name='dashboard-data-api'),
    path('user-profile/', views.user_profile_api, name='user-profile-api'),
    path('update-profile/', views.update_profile_api, name='update-profile-api'),
    path('interviews/', views.interviews_api, name='interviews-api'),
    path('get-schedules/', views.get_schedules_api, name='get-schedules-api'),
    path('get-available-schedules/', views.get_available_schedules_api, name='get-available-schedules-api'),
    path('camera-analysis/', views.camera_analysis_api, name='camera-analysis-api'),
    path('start-result/', views.start_result_api, name='start-result-api'),
    path('get-result/<int:interview_id>', views.get_result_api, name='get-result-api'),
    path('get-average-result/', views.get_average_score_api, name='get-average-result-api'),
    path('analyze-video/', views.analyze_video_api, name='analyze-video-api'),
    ##SCHEMA
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('profile/', views.UserProfileAPIView.as_view(), name='profile-api'),

    path('cv-screening/', views.CVScreeningAPIView.as_view(), name='cv-screening-api'),
    path('cv-screening/report/', views.CVScreeningReportListView.as_view(), name='cv-screening-report-api'),
    path('cv-screening/report/<int:pk>', views.CVScreeningReportDetailView.as_view(), name='cv-screening-report-detail-api'),

    # Optional UI:
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

]
