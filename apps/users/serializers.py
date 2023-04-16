from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')


class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'password')

        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        """
        Function which creates a new user in the database.
        """
        username = validated_data.get('username')
        password = validated_data.get('password')

        user = User.objects.create_user(
            username=username,
            password=password
        )

        return user