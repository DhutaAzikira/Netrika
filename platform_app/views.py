import os
import requests
from datetime import datetime
from django.db.models import Count, F, Q
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import serializers
from .serializers import RegisterSerializer, InterviewSerializer, ScheduleSerializer, UserProfileSerializer, \
    AvailableScheduleSerializer, ResultSerializer, QuestionSerializer, AnswerSerializer
from .models import Interviews, Schedules, UserProfiles, Results, Questions, Answers
from dotenv import load_dotenv

load_dotenv()

@extend_schema(
    summary="Authenticate with Google",
    description="Handles the callback from Google's OAuth2 flow to log in or register a user."
)
class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client

@extend_schema(
    summary="Register a new user",
    description="Creates a new user account with a username, email, and password.",
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(
            response=inline_serializer(
                name='UserCreationSuccess',
                fields={
                    'message': serializers.CharField(),
                    'user': inline_serializer(
                        name='UserDetail',
                        fields={
                            'username': serializers.CharField(),
                            'email': serializers.EmailField(),
                        }
                    )
                }
            ),
            description="User was created successfully."
        ),
        400: OpenApiResponse(description="Invalid data provided (e.g., username already exists, passwords don't match)."),
    }
)
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


@extend_schema(
    summary="Submit screener and schedule an interview",
    description="Submits interview details and a CV file. This triggers a webhook to schedule the interview and returns booking details.",
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'schedule_id': {'type': 'integer'},
                'date': {'type': 'string', 'format': 'date'},
                'posisi': {'type': 'string'},
                'industri': {'type': 'string'},
                'nama_perusahaan': {'type': 'string'},
                'tingkatan': {'type': 'string'},
                'jenis_wawancara': {'type': 'string'},
                'detail_pekerjaan': {'type': 'string'},
                'tier': {'type': 'string'},
                'cv': {'type': 'string', 'format': 'binary'},
            }
        }
    },
    responses={
        200: OpenApiResponse(
            response=inline_serializer(
                name='ScreenerSuccessResponse',
                fields={
                    'status': serializers.CharField(),
                    'message': serializers.CharField(),
                    'date': serializers.DateField(),
                    'start_time': serializers.TimeField(),
                    'end_time': serializers.TimeField(),
                    'posisi': serializers.CharField(),
                    'jenis_wawancara': serializers.CharField(),
                    'booking_code': serializers.CharField(),
                }
            ),
            description="Interview successfully scheduled via webhook."
        ),
        400: OpenApiResponse(description="Invalid or missing data, or CV file is required."),
        404: OpenApiResponse(description="User profile not found."),
    }
)
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

    if any(value is None or value == '' for value in n8n_data_payload.values()):
        return Response({"error": "Invalid data: Some required fields are missing or empty."},
                        status=status.HTTP_400_BAD_REQUEST)

    uploaded_file = request.FILES.get('cv')
    files_payload = {
        'cv': (uploaded_file.name, uploaded_file.read(), uploaded_file.content_type)
    }

    if not uploaded_file:
        return Response({"error": "CV file is required."}, status=status.HTTP_400_BAD_REQUEST)

    print(f"Sending data to n8n: {n8n_data_payload}")

    N8N_SCREENER_URL = os.getenv("N8N_SCREENER_URL")
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
    date = n8n_data.get('date')
    start_time = n8n_data.get('start_time')
    end_time = n8n_data.get('end_time')
    posisi = n8n_data.get('posisi')
    jenis_wawancara = n8n_data.get('jenis_wawancara')
    booking_code = n8n_data.get('booking_code')

    if not booking_code:
        return Response({"error": "Booking code not found."}, status=status.HTTP_400_BAD_REQUEST)

    response = {
        "status": response_status,
        "message": message,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "posisi": posisi,
        "jenis_wawancara": jenis_wawancara,
        "booking_code": booking_code
    }

    return Response(response, status=status.HTTP_200_OK)


@extend_schema(
    summary="Retrieve user profile",
    description="Gets the profile information for the authenticated user.",
    responses={
        200: UserProfileSerializer,
        404: OpenApiResponse(description="User profile not found."),
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_api(request):
    user = request.user
    try:
        user_profile = UserProfiles.objects.get(user=user)
        serializer = UserProfileSerializer(user_profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except UserProfiles.DoesNotExist:
        return Response({"error": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    summary="Update user profile",
    description="Updates the profile for the authenticated user. Use PATCH for partial updates.",
    request=UserProfileSerializer,
    responses={
        200: OpenApiResponse(
            response=inline_serializer(
                name='ProfileUpdateSuccess',
                fields={
                    'message': serializers.CharField(),
                    'data': UserProfileSerializer(),
                }
            ),
            description="Profile was updated successfully."
        ),
        400: OpenApiResponse(description="Invalid data provided."),
        404: OpenApiResponse(description="User profile not found."),
    }
)
@api_view(['PUT', 'PATCH']) #test2
@permission_classes([IsAuthenticated])
def update_profile_api(request):
    user = request.user
    try:
        user_profile = UserProfiles.objects.get(user=user)
    except UserProfiles.DoesNotExist:
        return Response({"error": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)
    serializer = UserProfileSerializer(instance=user_profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Profile updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="List user's interviews",
    description="Retrieves a list of all interviews scheduled by the authenticated user.",
    responses={
        200: InterviewSerializer(many=True),
        404: OpenApiResponse(description="User profile not found."),
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def interviews_api(request):
    user = request.user
    try:
        user_profile = UserProfiles.objects.get(user=user)
        interviews = Interviews.objects.filter(user_profile=user_profile)
        serializer = InterviewSerializer(interviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except UserProfiles.DoesNotExist:
        return Response({"error": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    deprecated=True,
    summary="[DEPRECATED] Retrieve dashboard data",
    description="This endpoint is deprecated. Please use the `/api/user-profile/` and `/api/interviews/` endpoints instead.",
    responses={
        200: OpenApiResponse(description="Returns a combination of user and interview data."),
        404: OpenApiResponse(description="User profile not found."),
    }
)
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


@extend_schema(
    deprecated=True,
    summary="[DEPRECATED] Get all schedule templates",
    description="This endpoint is deprecated. Please use `/api/get-available-schedules/` to get schedules for a specific date.",
    responses={200: ScheduleSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_schedules_api(request, date=None):
    try:
        schedules = Schedules.objects.all()
        serializer = ScheduleSerializer(schedules, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Get available interview schedules for a date",
    description="Retrieves all available interview slots for a given date, including the remaining capacity for each slot.",
    request=None,  # No request body for GET
    responses={
        200: AvailableScheduleSerializer(many=True),
        400: OpenApiResponse(description="Date field is required or has an invalid format."),
        500: OpenApiResponse(description="An internal server error occurred."),
    }
)
@api_view(['GET'])  # Change to GET method
@permission_classes([IsAuthenticated])
def get_available_schedules_api(request):
    target_date_str = request.query_params.get('date')  # Get date from query parameters
    if not target_date_str:
        return Response(
            {"error": "The 'date' field is required as a query parameter."},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response(
            {"error": "Date format must be YYYY-MM-DD."},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        available_schedules = Schedules.objects.annotate(
            booked_sessions=Count('interviews', filter=Q(interviews__date=target_date))
        ).annotate(
            remaining_capacity=3 - F('booked_sessions')
        ).order_by('start_time')

        serializer = AvailableScheduleSerializer(available_schedules, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": "An internal server error occurred."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@extend_schema(
    summary="Upload Image for Camera Analysis",
    description="""Uploads a single image during an interview for real-time analysis.
    This endpoint expects a `multipart/form-data` request containing the image and the corresponding interview ID.""",
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'image': {'type': 'string', 'format': 'binary'},
                'interview_id': {'type': 'integer'}
            },
            'required': ['image', 'interview_id']
        }
    },
    responses={
        200: OpenApiResponse(
            description="Image was successfully received and sent for analysis.",
            response=inline_serializer(
                name='CameraAnalysisSuccess',
                fields={'message': serializers.CharField()}
            )
        ),
        400: OpenApiResponse(description="No image file was provided in the request."),
        502: OpenApiResponse(description="Bad Gateway: The analysis service could not be reached or returned an error."),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def camera_analysis_api(request):
    if 'image' not in request.FILES:
        return Response({"error": "No image file provided."}, status=status.HTTP_400_BAD_REQUEST)

    image_file = request.FILES['image']
    files_payload = {
        'image': (image_file.name, image_file.read(), image_file.content_type)
    }
    interview_id = request.data.get('interview_id')

    N8N_CAMERA_ANALYSIS_URL = os.getenv("N8N_CAMERA_ANALYSIS_URL")
    try:
        n8n_response = requests.post(N8N_CAMERA_ANALYSIS_URL, data={"interview_id": interview_id}, files=files_payload)
        n8n_response.raise_for_status()
        n8n_data = n8n_response.json()
        print(f"n8n response data: {n8n_data}")
    except requests.exceptions.RequestException as e:
        # This will catch connection errors, timeouts, etc.
        return Response({"error": f"Failed to connect to analysis service: {e}"}, status=status.HTTP_502_BAD_GATEWAY)


    return Response({
        "message": "Image uploaded for analysis."
    }, status=status.HTTP_200_OK)


@extend_schema(
    summary="Start Final Result Analysis",
    description="Triggers the final analysis process for a completed interview.",
    request=inline_serializer(
        name='StartResultRequest',
        fields={'interview_id': serializers.IntegerField()}
    ),
    responses={
        200: OpenApiResponse(
            description="Result analysis process was started successfully.",
            response=inline_serializer(
                name='StartResultSuccess',
                fields={'message': serializers.CharField()}
            )
        ),
        400: OpenApiResponse(description="Interview ID is required."),
        500: OpenApiResponse(description="The analysis service failed to start the process."),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_result_api(request):
    interview_id = request.data.get('interview_id')
    if not interview_id:
        return Response({"error": "Interview ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    N8N_RESULT_URL = os.getenv("N8N_RESULT_URL")
    try:
        n8n_response = requests.post(N8N_RESULT_URL, json={"interview_id": interview_id})
        n8n_response.raise_for_status()
        n8n_data = n8n_response.json()
        print(f"n8n response data: {n8n_data}")
    except requests.exceptions.RequestException as e:
        return Response({"error": f"Failed to connect to result service: {e}"}, status=status.HTTP_502_BAD_GATEWAY)

    if n8n_data.get('status') != 200:
        return Response({"error": "Failed to start result analysis."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        "message": "Result analysis started successfully."
    }, status=status.HTTP_200_OK)


@extend_schema(
    summary="Get Complete Interview Result",
    description="Retrieves the full results for a specific interview, including scores, questions, and answers.",
    responses={
        200: OpenApiResponse(
            description="The full result data for the interview.",
            response=inline_serializer(
                name='FullInterviewResult',
                fields={
                    'interview': InterviewSerializer(),
                    'result': ResultSerializer(allow_null=True),
                    'questions': QuestionSerializer(many=True),
                    'answers': AnswerSerializer(many=True),
                }
            )
        ),
        404: OpenApiResponse(description="Interview with the specified ID was not found."),
        500: OpenApiResponse(description="An unexpected server error occurred."),
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_result_api(request, interview_id):
    if not interview_id:
        return Response({"error": "Interview ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        interview = Interviews.objects.get(id=interview_id)
        interview_serializer = InterviewSerializer(interview)

        # Fetch related data
        questions = Questions.objects.filter(interview_id=interview_id)
        question_ids = questions.values_list('id', flat=True)
        answers = Answers.objects.filter(question_id__in=question_ids)

        question_serializer = QuestionSerializer(questions, many=True)
        answer_serializer = AnswerSerializer(answers, many=True)

        result_data = None
        try:
            result = Results.objects.get(interview_id=interview_id)
            result_data = ResultSerializer(result).data
        except Results.DoesNotExist:
            # It's okay if a result doesn't exist yet, we can pass null
            pass

        # Structure the final response
        data = {
            "interview": interview_serializer.data,
            "result": result_data,
            "questions": question_serializer.data,
            "answers": answer_serializer.data,
        }

        return Response(data, status=status.HTTP_200_OK)
    except Interviews.DoesNotExist:
        return Response({"error": "Interview not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
