from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render
import requests
from PlatformInterview import settings
from .serializers import RegisterSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Interview # Make sure to import your Interview model
from .serializers import RegisterSerializer, InterviewSerializer, ScheduleSerializer
# Add your Interview model to the imports
from .models import Interview, Schedule

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


# Replace your existing submit_screener_api function with this one

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def submit_screener_api(request):
    """
    This is the final version of the screener submission API.
    It receives form data, adds the user's ID, and forwards it all to n8n.
    """
    try:
        # 1. Get the securely authenticated user from the request token.
        user = request.user

        # 2. Get the chosen schedule_id from the form data sent by the JavaScript.
        schedule_id = request.data.get('schedule_id')
        if not schedule_id:
            return Response({"error": "A schedule_id must be selected."}, status=status.HTTP_400_BAD_REQUEST)

        # 3. (Good practice) Look up the actual Schedule object to make sure it's valid.
        try:
            schedule_object = Schedule.objects.get(pk=schedule_id)
        except Schedule.DoesNotExist:
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
        Interview.objects.create(
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


# ... inside your dashboard_data_api view ...

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_data_api(request):
    user = request.user

    # The query to get interviews remains the same
    interviews = Interview.objects.filter(user=user)
    interview_serializer = InterviewSerializer(interviews, many=True)

    # The fix is here: We now construct the data dictionary so that 'username'
    # is always included, regardless of whether the 'interviews' list is empty.
    data = {
        'username': user.username,
        'interviews': interview_serializer.data
    }
    return Response(data)

# Add this new view at the bottom
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_schedules_api(request):
    """
    Fetches all available schedules from the database.
    """
    try:
        # For now, we get all schedules. Later, you could filter for future dates.
        schedules = Schedule.objects.all()
        serializer = ScheduleSerializer(schedules, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
