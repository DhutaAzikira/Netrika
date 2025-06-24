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
    try:
        # 1. Get the securely authenticated user from the request token.
        user = request.user

        # 2. Get the chosen schedule_id from the form data sent by the JavaScript.
        schedule_id = request.data.get('schedule_id')
        if not schedule_id:
            return Response({"error": "A schedule_id must be selected."}, status=status.HTTP_400_BAD_REQUEST)

        # 3. (Good practice) Look up the actual Schedule object to make sure it's valid.
        try:
            schedule_object = Schedules.objects.get(pk=schedule_id)
        except Schedules.DoesNotExist:
            return Response({"error": "The selected schedule is not valid."}, status=status.HTTP_400_BAD_REQUEST)

        # 4. Prepare the data payload for n8n, now including both IDs.
        n8n_data_payload = {
            'userId': user.id,
            'scheduleId': schedule_id,
            'Name': request.data.get('Name'),
            'Position': request.data.get('Position'),
            'JobDescription': request.data.get('JobDescription'),
        }

        # 5. Prepare the file payload.
        uploaded_file = request.FILES.get('data')
        if not uploaded_file:
            return Response({"error": "CV/Resume file not provided."}, status=status.HTTP_400_BAD_REQUEST)

        files_payload = {
            'data': (uploaded_file.name, uploaded_file.read(), uploaded_file.content_type)
        }

        # 6. Send everything to the n8n scheduling webhook.
        print(f"Sending data to n8n: {n8n_data_payload}")
        n8n_response = requests.post(
            settings.N8N_SCREENER_URL,
            data=n8n_data_payload,
            files=files_payload
        )
        n8n_response.raise_for_status()
        n8n_data = n8n_response.json()
        session_id = n8n_data.get('sessionId')  # Get the live session ID from n8n

        # 7. Create the official Interview record in our database, linking user and schedule.
        Interviews.objects.create(
            user=user,
            schedule=schedule_object,
            session_id=session_id,
            position=n8n_data_payload.get('Position'),
            status="Ready to Start"
        )

        return Response({"message": "Successfully scheduled interview! Redirecting to dashboard..."},
                        status=status.HTTP_201_CREATED)

    except requests.exceptions.RequestException as e:
        return Response({'error': f"Failed to contact n8n: {e}"}, status=502)
    except Exception as e:
        return Response({'error': f"An unexpected error occurred: {str(e)}"}, status=500)


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
