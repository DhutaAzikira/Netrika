from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token # Import this

urlpatterns = [
    path('register/', views.register_api, name='register-api'),
    path('login/', obtain_auth_token, name='login-api'), # Add this line.
    path('submit-screener/', views.submit_screener_api, name='submit-screener-api'),
    path('dashboard-data/', views.dashboard_data_api, name='dashboard-data-api'),
    path('get-schedules/', views.get_schedules_api, name='get-schedules-api'),

]