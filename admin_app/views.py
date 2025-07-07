from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser

from .models import Packages
from .serializers import PackageSerializer

class PackageViewSet(ModelViewSet):
    """
    A ViewSet for creating, viewing, and editing packages.
    Only accessible by admin users.
    """
    queryset = Packages.objects.all().order_by('price')
    serializer_class = PackageSerializer
    permission_classes = [IsAdminUser]