from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [

path('register/', views.register_page_view, name='register-page'),
path('login/', views.login_page_view, name='login-page'),

path('screener/', views.screener_view, name='screener-page'),

path('dashboard/', views.dashboard_view, name='dashboard-page'),
]