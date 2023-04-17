from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model: type = User
        fields: tuple = ('id', 'username')


class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'password')

        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data: dict) -> User:
        """
        Function which creates a new user in the database.
        """
        username = validated_data.get('username')
        password = validated_data.get('password')

        user: User = User.objects.create_user(
            username=username,
            password=password
        )

        return user
