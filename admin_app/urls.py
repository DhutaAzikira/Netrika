from rest_framework.routers import DefaultRouter
from .views import PackageViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'packages', PackageViewSet, basename='package')

# The API URLs are now determined automatically by the router.
urlpatterns = router.urls