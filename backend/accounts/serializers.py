from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserSignupSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=6, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, min_length=6, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('name', 'email', 'password', 'confirm_password')

    def validate_email(self, value):
        # Django User model stores username. Since we map username to email,
        # checking both ensures no duplicates.
        if User.objects.filter(email=value).exists() or User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        # We create the user, mapping the name to first_name and email to username.
        user = User.objects.create(
            username=validated_data['email'],
            email=validated_data['email'],
            first_name=validated_data['name'],
            password=make_password(validated_data['password'])
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    # Map email to username for SimpleJWT validation
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the default username field dynamically added by SimpleJWT
        if 'username' in self.fields:
            del self.fields['username']

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        # SimpleJWT's validator expects username to match USERNAME_FIELD
        attrs['username'] = email
        
        data = super().validate(attrs)
        
        # Add basic user details for the frontend convenience
        data['user'] = {
            'name': self.user.first_name,
            'email': self.user.email
        }
        return data

