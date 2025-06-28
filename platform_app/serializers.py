from django.contrib.auth.models import User
from platform_app.models import Interviews, Schedules, UserProfiles, Results, Questions, Answers
from rest_framework import serializers, validators
from django.contrib.auth import get_user_model
from dj_rest_auth.models import TokenModel


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password', 'email')
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {
                "required": True,
                "allow_blank": False,
                "validators": [
                    validators.UniqueValidator(
                        User.objects.all(), "A user with that Email already exists."
                    )
                ],
            },
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class InterviewSerializer(serializers.ModelSerializer):
    # This nested class tells the serializer how to handle related models
    class UserSerializer(serializers.ModelSerializer):
        class Meta:
            model = User
            fields = ['username', 'email']  # Only show these user fields

    user = UserSerializer(read_only=True)  # Use the nested serializer for the user field

    class Meta:
        model = Interviews
        fields = '__all__'


# Add this new serializer at the bottom
class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedules
        fields = ['id', 'start_time', 'end_time']


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfiles
        fields = '__all__'


class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('pk', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = ('email',)


class CustomTokenSerializer(serializers.ModelSerializer):
    user = UserDetailsSerializer(read_only=True)

    class Meta:
        model = TokenModel
        fields = ('key', 'user')


class AvailableScheduleSerializer(serializers.ModelSerializer):
    booked_sessions = serializers.IntegerField(read_only=True)
    remaining_capacity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Schedules
        fields = [
            'id',
            'start_time',
            'end_time',
            'booked_sessions',
            'remaining_capacity'
        ]


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Results
        fields = '__all__'

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questions
        fields = '__all__'

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answers
        fields = ['id', 'question_id', 'answer']