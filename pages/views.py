from django.shortcuts import render
from django.contrib.auth.decorators import login_required # Import this

from platform_app.models import Interviews


def register_page_view(request):
    return render(request, 'pages/register.html')

def login_page_view(request):
    return render(request, 'pages/login.html')


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
# Make sure to import the Interview model from your platform_app
from platform_app.models import Interviews


# ... other views ...

def dashboard_view(request):
    # This view's only job is now to serve the empty HTML shell.
    # The JavaScript will handle everything else.
    return render(request, 'pages/dashboard.html')

def screener_view(request):
    return render(request, 'pages/screener_form.html')


def interview_page_view(request):
    return render(request, 'pages/interview.html')