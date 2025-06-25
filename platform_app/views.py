import profile

from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status
import requests
from PlatformInterview import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import RegisterSerializer, InterviewSerializer, ScheduleSerializer, UserProfileSerializer
from .models import Interviews, Schedules, UserProfiles


@api_view(['POST'])
def register_api(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            "message": "User created successfully",
            "user": {
                "username": user.username,
                "email": user.email
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def submit_screener_api(request):
    user = request.user

    try:
        user_profile = UserProfiles.objects.get(user=user)
    except UserProfiles.DoesNotExist:
        return Response({"error": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)


    schedule_id = request.data.get('schedule_id')
    date = request.data.get('date')
    posisi = request.data.get('posisi')
    industri = request.data.get('industri')
    nama_perusahaan = request.data.get('nama_perusahaan')
    tingkatan = request.data.get('tingkatan')
    jenis_wawancara = request.data.get('jenis_wawancara')
    detail_pekerjaan = request.data.get('detail_pekerjaan')
    tier = request.data.get('tier', 'Free')  # Default to 'Free' if not provided

    n8n_data_payload = {
        'user_profile_id': user_profile.id,
        'schedule_id': schedule_id,
        'date': date,
        'posisi': posisi,
        'industri': industri,
        'nama_perusahaan': nama_perusahaan,
        'tingkatan': tingkatan,
        'jenis_wawancara': jenis_wawancara,
        'detail_pekerjaan': detail_pekerjaan,
        'tier': tier,
    }

    uploaded_file = request.FILES.get('cv')
    files_payload = {
        'cv': (uploaded_file.name, uploaded_file.read(), uploaded_file.content_type)
    }

    print(f"Sending data to n8n: {n8n_data_payload}")
    N8N_SCREENER_URL = "http://localhost:5678/webhook/schedule-interview"
    n8n_response = requests.post(
        N8N_SCREENER_URL,
        data=n8n_data_payload,
        files=files_payload
    )

    n8n_response.raise_for_status()
    n8n_data = n8n_response.json()

    print(f"n8n response data: {n8n_data}")

    response_status = n8n_data['status']
    message = n8n_data['message']
    booking_code = n8n_data.get('booking_code')

    if not booking_code:
        return Response({"error": "Booking code not found."}, status=status.HTTP_400_BAD_REQUEST)

    response = {
        "status": response_status,
        "message": message,
        "booking_code": booking_code
    }


    return Response(response, status=status.HTTP_200_OK)

    ##TODO Error Validations



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_data_api(request):
    user = request.user
    try:
        user_profile = UserProfiles.objects.get(user=user)

        user_profile_serializer = UserProfileSerializer(user_profile)
        profile_data = user_profile_serializer.data

        print(user)
        print(f"User profile data: {profile_data}")
        print(f"User data: {user_profile}")


    except UserProfiles.DoesNotExist:
        return Response({"error": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)

    interviews = Interviews.objects.filter(user_profile=user_profile)
    interview_serializer = InterviewSerializer(interviews, many=True)

    data = {
        'user_id': user_profile.id,
        'username': user.username,
        'full_name': user_profile.full_name,
        'phone_number': user_profile.phone_number,
        'email': user_profile.email,
        'date_of_birth': user_profile.date_of_birth,
        'sex': user_profile.sex,
        'interviews': interview_serializer.data
    }


    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_schedules_api(request):
    try:
        schedules = Schedules.objects.all()
        serializer = ScheduleSerializer(schedules, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
