from django.contrib.auth.models import User
from platform_app.models import Interview, Schedule
from rest_framework import serializers, validators

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
            fields = ['username', 'email'] # Only show these user fields

    user = UserSerializer(read_only=True) # Use the nested serializer for the user field

    class Meta:
        model = Interview
        fields = '__all__'



# Add this new serializer at the bottom
class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ['id', 'date', 'start_time', 'end_time']