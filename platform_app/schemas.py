# schemas.py
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, inline_serializer
from rest_framework import serializers

from platform_app.serializers import InterviewSerializer, ResultSerializer, QuestionSerializer, AnswerSerializer, \
    ScheduleSerializer, AvailableScheduleSerializer, UserProfileSerializer, CVScreeningReportSerializer

"""
# ===================================================================
# 👤 User: Authentication & Onboarding
# ===================================================================
"""

GoogleLoginSchema = {
    "tags": ["User: Authentication & Onboarding"],
    "summary": "Google Login/Signup (Access Token)",
    "description": "Authenticates users via a Google access token obtained from the client-side login.",
    "request": inline_serializer(
        name='GoogleAccessTokenRequest',
        fields={
            'access_token': serializers.CharField(
                help_text="The access token provided by Google's OAuth2 flow."
            )
        }
    ),
    "responses": {
        200: OpenApiResponse(
            description="Successful authentication. Returns a session key and user details.",
            response=inline_serializer(
                name='AuthTokenResponse',
                fields={
                    'key': serializers.CharField(
                        help_text="The authentication token (key) for subsequent API requests."
                    ),
                    'user': inline_serializer(
                        name='UserAuthDetail',
                        fields={
                            'pk': serializers.IntegerField(),
                            'username': serializers.CharField(),
                            'email': serializers.EmailField(),
                            'first_name': serializers.CharField(),
                            'last_name': serializers.CharField()
                        }
                    )
                }
            )
        ),
        400: OpenApiResponse(description="Invalid request or authentication failed"),
    }
}

from rest_framework import serializers
from drf_spectacular.utils import OpenApiResponse, inline_serializer

RegisterSchema = {
    "tags": ["User: Authentication & Onboarding"],
    "summary": "User Registration",
    "description": "Registers a new user with a username, email, and password. On success, it returns the user's details and an authentication token.",
    "request": inline_serializer(
        name='RegisterRequest',
        fields={
            'username': serializers.CharField(),
            'password': serializers.CharField(write_only=True), # Password should not be readable
            'email': serializers.EmailField(),
        }
    ),
    "responses": {
        201: OpenApiResponse(
            description="User created successfully. The response includes user details and an auth token.",
            response=inline_serializer(
                name='RegisterSuccessResponse',
                fields={
                    'message': serializers.CharField(),
                    'user': inline_serializer(
                        name='RegisteredUser',
                        fields={
                            'username': serializers.CharField(),
                            'email': serializers.EmailField(),
                        }
                    ),
                    'token': serializers.CharField(),
                }
            )
        ),
        400: OpenApiResponse(
            description="Invalid data provided (e.g., username already exists, invalid email).",
            response=inline_serializer(
                name='RegisterErrorResponse',
                fields={
                    'field_name': serializers.ListField(child=serializers.CharField())
                }
            )
        ),
    }
}

"""
# ===================================================================
# 🗓️ User: Interview Scheduling
# ===================================================================
"""

SubmitScreenerSchema = {
    "tags": ["User: Interview Scheduling"],
    "summary": "Submit screener and schedule an interview",
    "description": "Submits interview details and a CV file to schedule an interview.",
    "request": {
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'schedule_id': {'type': 'integer'}, 'date': {'type': 'string', 'format': 'date'},
                'posisi': {'type': 'string'}, 'industri': {'type': 'string'},
                'nama_perusahaan': {'type': 'string'}, 'tingkatan': {'type': 'string'},
                'jenis_wawancara': {'type': 'string'}, 'detail_pekerjaan': {'type': 'string'},
                'tier': {'type': 'string'}, 'cv': {'type': 'string', 'format': 'binary'},
            }
        }
    },
    "responses": {
        200: OpenApiResponse(description="Interview successfully scheduled."),
        400: OpenApiResponse(description="Invalid or missing data."),
        404: OpenApiResponse(description="User profile not found."),
    }
}

GetAvailableScheduleSchema = {
    "tags": ["User: Interview Scheduling"],
    "summary": "Get available interview schedules",
    "description": "Retrieves available interview slots for a given date.",
    "responses": {
        200: AvailableScheduleSerializer,
        400: OpenApiResponse(description="Date field is required or invalid."),
        500: OpenApiResponse(description="An internal server error occurred."),
    }
}

"""
# ===================================================================
# 🎙️ User: Interview Management
# ===================================================================
"""

InterviewsSchema = {
    "tags": ["User: Interview Management"],
    "summary": "List user's interviews",
    "description": "Retrieves a list of all interviews scheduled by the authenticated user.",
    "responses": {
        200: InterviewSerializer,
        404: OpenApiResponse(description="User profile not found."),
    }
}

"""
# ===================================================================
# 📹 User: Live Interview Actions
# ===================================================================
"""

"""
# ===================================================================
# 📊 User: Results & Statistics
# ===================================================================
"""

StartResultSchema = {
    "tags": ["User: Results & Statistics"],
    "summary": "Start Final Result Analysis",
    "description": "Triggers the final analysis process for a completed interview.",
    "request": inline_serializer(name='StartResultRequest', fields={'interview_id': serializers.IntegerField()}),
    "responses": {
        200: OpenApiResponse(description="Result analysis started."),
        400: OpenApiResponse(description="Interview ID is required."),
    }
}

GetResultSchema = {
    "tags": ["User: Results & Statistics"],
    "summary": "Get Complete Interview Result",
    "description": "Retrieves the full results for a specific interview.",
    "responses": {
        200: OpenApiResponse(
            response=inline_serializer(
                name='FullInterviewResult',
                fields={
                    'interview': InterviewSerializer(),
                    'result': ResultSerializer(allow_null=True),
                    'questions': serializers.ListField(child=QuestionSerializer()),
                    'answers': serializers.ListField(child=AnswerSerializer()),
                }
            )
        ),
        404: OpenApiResponse(description="Interview not found."),
    }
}

"""
# ===================================================================
# ⚠️ Deprecated
# ===================================================================
"""

DashboardDataSchema = {
    "summary": "[DEPRECATED] Retrieve dashboard data",
    "description": "This endpoint is deprecated. Please use `/api/profile/` and `/api/interviews/` instead.",
    "responses": {200: OpenApiResponse(description="Deprecated data object.", response={})}
}

GetSchedulesSchema = {
    "summary": "[DEPRECATED] Get all schedule templates",
    "description": "This endpoint is deprecated. Please use `/api/get-available-schedules/` instead.",
    "responses": {200: ScheduleSerializer}

}

UserProfileSchema = {
    # "tags": ["User: Authentication & Onboarding"],
    "summary": "Retrieve user profile",
    "description": "Gets the profile information for the authenticated user.",
    "responses": {
        200: UserProfileSerializer,
        404: OpenApiResponse(description="User profile not found."),
    }
}

UpdateProfileSchema = {
    # "tags": ["User: Authentication & Onboarding"],
    "summary": "Update user profile",
    "description": "Updates the profile for the authenticated user. Use PATCH for partial updates.",
    "request": UserProfileSerializer,
    "responses": {
        200: OpenApiResponse(
            response=inline_serializer(
                name='ProfileUpdateSuccess',
                fields={'message': serializers.CharField(), 'data': UserProfileSerializer()}
            ),
            description="Profile was updated successfully."
        ),
        400: OpenApiResponse(description="Invalid data provided."),
        404: OpenApiResponse(description="User profile not found."),
    }
}

GetAverageScoreSchema = {
    # "tags": ["User: Results & Statistics"],
    "summary": "Get User's Average Interview Score",
    "description": "Calculates the average `final_score` across all of the user's interviews.",
    "responses": {
        200: OpenApiResponse(
            response=inline_serializer(
                name='AverageScoreResponse',
                fields={
                    'average_score': serializers.CharField(),
                    'message': serializers.CharField(required=False)
                }
            )
        ),
        404: OpenApiResponse(description="User profile not found."),
    }
}

CameraAnalysisSchema = {
    # "tags": ["User: Live Interview Actions"],
    "summary": "Upload Image for Camera Analysis",
    "description": "Uploads an image during an interview for real-time analysis.",
    "request": {
        'multipart/form-data': {
            'type': 'object',
            'properties': {'image': {'type': 'string', 'format': 'binary'}, 'interview_id': {'type': 'integer'}},
            'required': ['image', 'interview_id']
        }
    },
    "responses": {
        200: OpenApiResponse(description="Image received for analysis."),
        400: OpenApiResponse(description="No image file provided."),
        502: OpenApiResponse(description="Analysis service could not be reached."),
    }
}

AnalyzeVideoSchema = {
    # "tags": ["User: Live Interview Actions"],
    "summary": "Analyze a video and return a summary",
    "description": "Uploads a video file for AI analysis and returns a summary.",
    "request": {
        "multipart/form-data": {
            "type": "object",
            "properties": {"video_file": {"type": "string", "format": "binary"}},
        }
    },
    "responses": {
        200: OpenApiResponse(response={"type": "object", "properties": {"summary": {"type": "string"}}}),
        400: OpenApiResponse(description="Invalid input."),
    }
}

CVScreeningSchema = {
    "tags": ["User: CV Screening"],
    "summary": "Submit CV for Screening",
    "description": "Uploads a CV file for AI analysis. The system processes it synchronously and returns a detailed screening report.",
    "request": {
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'cv': {'type': 'string', 'format': 'binary'}
            },
            'required': ['cv']
        }
    },
    "responses": {
        201: CVScreeningReportSerializer,
        400: OpenApiResponse(description="No CV file was provided."),
        502: OpenApiResponse(description="Bad Gateway: The AI analysis service returned an error."),
        504: OpenApiResponse(description="Gateway Timeout: The AI analysis service could not be reached."),
        500: OpenApiResponse(description="Internal Server Error: The data returned by the AI service was invalid."),
    }
}
