from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import UserProfile
User = get_user_model()


MAX_PROFILE_PICTURE_SIZE = 5 * 1024 * 1024
ALLOWED_PROFILE_PICTURE_TYPES = {
    'image/jpeg',
    'image/png',
    'image/webp',
}


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)



class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.full_name', required=False, allow_blank=True)
    subscription_status = serializers.CharField(source='user.subscription_status', read_only=True)
    subscription_plan = serializers.CharField(source='user.subscription_plan', read_only=True)
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'username',
            'email',
            'full_name',
            'subscription_status',
            'subscription_plan',
            'bio',
            'profile_picture',
            'profile_picture_url',
            'phone_number',
            'date_of_birth',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_profile_picture_url(self, obj):
        if not obj.profile_picture:
            return None

        request = self.context.get('request')
        url = obj.profile_picture.url
        if request:
            return request.build_absolute_uri(url)
        return url

    def validate_profile_picture(self, value):
        if value.size > MAX_PROFILE_PICTURE_SIZE:
            raise serializers.ValidationError("Profile picture must be 5MB or smaller.")

        content_type = getattr(value, 'content_type', None)
        if content_type not in ALLOWED_PROFILE_PICTURE_TYPES:
            raise serializers.ValidationError("Upload a JPEG, PNG, or WEBP image.")

        return value

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        full_name = user_data.get('full_name')

        if full_name is not None:
            instance.user.full_name = full_name
            instance.user.save(update_fields=['full_name'])

        return super().update(instance, validated_data)


class ProfilePictureSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'profile_picture_url']

    def get_profile_picture_url(self, obj):
        if not obj.profile_picture:
            return None

        request = self.context.get('request')
        url = obj.profile_picture.url
        if request:
            return request.build_absolute_uri(url)
        return url

    def validate_profile_picture(self, value):
        if value.size > MAX_PROFILE_PICTURE_SIZE:
            raise serializers.ValidationError("Profile picture must be 5MB or smaller.")

        content_type = getattr(value, 'content_type', None)
        if content_type not in ALLOWED_PROFILE_PICTURE_TYPES:
            raise serializers.ValidationError("Upload a JPEG, PNG, or WEBP image.")

        return value


# Password Reset Serializers
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No account found with this email.")
        return value

class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
