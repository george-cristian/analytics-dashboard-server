from django.contrib.auth import login
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.authtoken.serializers import AuthTokenSerializer
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView
from django.http import HttpRequest

from .serializers import RegisterSerializer, UserSerializer


class RegisterAPI(generics.GenericAPIView):
    """
    View for the register API.
    """
    serializer_class = RegisterSerializer

    def post(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        Post function to register a new user.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        _, token = AuthToken.objects.create(user)

        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": token
        })


class LoginAPI(KnoxLoginView):
    """
    View for the loging API using knox to manage authentication tokens.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request: HttpRequest, format: str = None) -> Response:
        """
        Post function to login a user.
        """
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        login(request, user)

        return super(LoginAPI, self).post(request, format=None)
