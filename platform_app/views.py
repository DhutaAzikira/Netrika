import os
import random

import requests
from datetime import datetime
from django.db.models import Count, F, Q, Avg
from django.http import Http404
from google.genai import types
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status, serializers, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework.views import APIView
from .schemas import GoogleLoginSchema, RegisterSchema, SubmitScreenerSchema, UserProfileSchema, UpdateProfileSchema, \
    InterviewsSchema, GetAvailableScheduleSchema, CameraAnalysisSchema, StartResultSchema, GetResultSchema, \
    GetAverageScoreSchema, DashboardDataSchema, GetSchedulesSchema, AnalyzeVideoSchema
from .serializers import RegisterSerializer, InterviewSerializer, ScheduleSerializer, UserProfileSerializer, \
    AvailableScheduleSerializer, ResultSerializer, QuestionSerializer, AnswerSerializer, UserProfilesSerializer, \
    CVScreeningReportSerializer
from .models import Interviews, Schedules, UserProfiles, Results, Questions, Answers, CVScreeningReport
from dotenv import load_dotenv

load_dotenv()


@extend_schema(**GoogleLoginSchema)
class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client


@extend_schema(**RegisterSchema)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            "message": "User created successfully",
            "user": {
                "username": user.username,
                "email": user.email
            },
            "token": token.key  # Return the token's key
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(**SubmitScreenerSchema)
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
    package = request.data.get('package')

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
        'package': package,
    }

    if any(value is None or value == '' for key, value in n8n_data_payload.items()
           if key != 'nama_perusahaan'):
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
        "start_time": start_time[:8],
        "end_time": end_time[:8],
        "posisi": posisi,
        "jenis_wawancara": jenis_wawancara,
        "booking_code": booking_code
    }

    return Response(response, status=status.HTTP_200_OK)


@extend_schema(**InterviewsSchema)
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


@extend_schema(**GetAvailableScheduleSchema)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_schedules_api(request):
    target_date_str = request.query_params.get('date')
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


@extend_schema(**StartResultSchema)
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


@extend_schema(**GetResultSchema)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_result_api(request, interview_id):
    if not interview_id:
        return Response({"error": "Interview ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        interview = Interviews.objects.get(id=interview_id)
        interview_serializer = InterviewSerializer(interview)

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
            pass
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


@permission_classes([IsAuthenticated])
class UserProfileAPIView(APIView):
    def _get_object(self, user):
        try:
            return UserProfiles.objects.get(user=user)
        except UserProfiles.DoesNotExist:
            raise Http404

    @extend_schema(
        summary="Retrieve User Profile",
        description="Fetches the profile details for the currently authenticated user.",
        responses={
            200: UserProfilesSerializer,
            404: OpenApiResponse(description="User profile not found."),
        }
    )
    def get(self, request):
        profile = self._get_object(request.user)
        serializer = UserProfilesSerializer(profile)
        return Response(serializer.data)

    @extend_schema(
        summary="Create User Profile",
        description="Creates a profile for the currently authenticated user. A user can only have one profile.",
        request=inline_serializer(
            name='UserProfileCreateSerializer',
            fields={
                'full_name': serializers.CharField(required=True, max_length=255),
                'phone_number': serializers.CharField(required=True, max_length=15),
                'email': serializers.EmailField(required=True),
                'date_of_birth': serializers.DateField(required=True),
                'gender': serializers.ChoiceField(choices=['Laki-laki', 'Perempuan'], required=True),
                'profile_picture': serializers.ImageField(required=False, allow_null=True),
                'bio': serializers.CharField(required=False, allow_blank=True, max_length=500)
            },
        ),
        responses={
            201: UserProfilesSerializer,
            400: OpenApiResponse(description="Invalid data provided or a profile for this user already exists."),
        }
    )
    def post(self, request):
        if UserProfiles.objects.filter(user=request.user).exists():
            return Response(
                {"error": "Profile already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = UserProfilesSerializer(data=request.data)
        if serializer.is_valid():
            current_time = datetime.now().strftime('%Y%m%d%H%M%S')
            random_suffix = str(random.randint(100, 999))
            unique_id = f"{current_time}{random_suffix}"
            serializer.save(user=request.user, id=unique_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Update User Profile (Full)",
        description="Performs a full update of the user's profile. All fields must be provided.",
        request=UserProfilesSerializer,
        responses={
            200: UserProfilesSerializer,
            400: OpenApiResponse(description="Invalid data provided."),
            404: OpenApiResponse(description="User profile not found."),
        }
    )
    def put(self, request):
        profile = self._get_object(request.user)
        serializer = UserProfilesSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Partially Update User Profile",
        description="Performs a partial update of the user's profile. Only the fields to be changed need to be provided.",
        request=UserProfilesSerializer,
        responses={
            200: UserProfilesSerializer,
            400: OpenApiResponse(description="Invalid data provided."),
            404: OpenApiResponse(description="User profile not found."),
        }
    )
    def patch(self, request):
        profile = self._get_object(request.user)
        serializer = UserProfilesSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
class CVScreeningAPIView(APIView):

    def post(self, request):
        cv_file = request.FILES.get('cv')
        if not cv_file:
            return Response({"error": "No CV file provided."}, status=status.HTTP_400_BAD_REQUEST)

        # --- Call n8n Synchronously using requests ---
        n8n_webhook_url = os.getenv('N8N_CV_SCREENER_URL')
        files = {'cv': (cv_file.name, cv_file.read(), cv_file.content_type)}

        current_time = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = str(random.randint(100, 999))
        unique_id = f"CVR-{current_time}-{random_suffix}"

        try:
            response = requests.post(n8n_webhook_url,json={"id":unique_id}, files=files, timeout=90)  # 60-second timeout
            response.raise_for_status()  # Raises an exception for 4xx/5xx errors
            n8n_data = response.json()

        except requests.exceptions.HTTPError as e:
            return Response({"error": "Failed to get analysis from AI service.", "details": str(e)},
                            status=status.HTTP_502_BAD_GATEWAY)
        except requests.exceptions.RequestException as e:
            return Response({"error": "Network error while contacting AI service.", "details": str(e)},
                            status=status.HTTP_504_GATEWAY_TIMEOUT)

        serializer = CVScreeningReportSerializer(data=n8n_data)
        if serializer.is_valid():
            # Generate the unique ID string
            current_time = datetime.now().strftime('%Y%m%d%H%M%S')
            random_suffix = str(random.randint(100, 999))
            unique_id = f"{current_time}{random_suffix}"

            # Save the validated data, passing in the user and the custom id
            serializer.save(user=request.user, id=unique_id)

            # We return the serializer's data, which now includes the new ID
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@permission_classes([IsAuthenticated])
class CVScreeningReportListView(generics.ListAPIView):
    serializer_class = CVScreeningReportSerializer

    def get_queryset(self):
        return CVScreeningReport.objects.filter(user=self.request.user).order_by('-created_at')


@permission_classes([IsAuthenticated])
class CVScreeningReportDetailView(generics.RetrieveAPIView):
    serializer_class = CVScreeningReportSerializer

    def get_queryset(self):
        return CVScreeningReport.objects.filter(user=self.request.user)


"""
========================================================================================================
                                         DEPRECATED ZONE
========================================================================================================
"""


@extend_schema(**DashboardDataSchema, deprecated=True, tags=["DEPRECATED"])
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
        'date_of_birth': user_profile.date_of_birth,
        'gender': user_profile.gender,
        'interviews': interview_serializer.data
    }

    return Response(data)


@extend_schema(**GetSchedulesSchema, deprecated=True, tags=["DEPRECATED"])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_schedules_api(request, date=None):
    try:
        schedules = Schedules.objects.all()
        serializer = ScheduleSerializer(schedules, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(**CameraAnalysisSchema, deprecated=True, tags=["DEPRECATED"])
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
        return Response({"error": f"Failed to connect to analysis service: {e}"}, status=status.HTTP_502_BAD_GATEWAY)

    return Response({
        "message": "Image uploaded for analysis."
    }, status=status.HTTP_200_OK)


@extend_schema(**AnalyzeVideoSchema, deprecated=True, tags=["DEPRECATED"])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_video_api(request):
    from google import genai

    client = genai.Client(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))

    video_file_name = "a.mp4"
    video_bytes = open(video_file_name, 'rb').read()

    response = client.models.generate_content(
        model='models/gemini-2.0-flash',
        contents=types.Content(
            parts=[
                types.Part(
                    inline_data=types.Blob(data=video_bytes, mime_type='video/mp4')
                ),
                types.Part(text='Please summarize the video in 3 sentences.')
            ]
        )
    )
    pass


@extend_schema(**GetAverageScoreSchema, deprecated=True, tags=["DEPRECATED"])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_average_score_api(request):
    user = request.user
    try:
        user_profile = UserProfiles.objects.get(user=user)
    except UserProfiles.DoesNotExist:
        return Response({"error": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)

    average_score = Results.objects.filter(interview__user_profile=user_profile).aggregate(
        average_score=Avg('final_score')
    )['average_score']

    if average_score is None:
        return Response({
            "message": "No results found for this user.",
            "average_score": "-"
        }, status=status.HTTP_200_OK)
    return Response({"average_score": f"{average_score:.2f}"}, status=status.HTTP_200_OK)


@extend_schema(**UserProfileSchema, deprecated=True, tags=["DEPRECATED"])
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


@extend_schema(**UpdateProfileSchema, deprecated=True, tags=["DEPRECATED"])
@api_view(['PUT', 'PATCH'])
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
