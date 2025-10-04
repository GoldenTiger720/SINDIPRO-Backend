from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import UserRegistrationSerializer, UserSerializer, UserProfileSerializer

User = get_user_model()

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegistrationSerializer
    authentication_classes = []  # Disable authentication for registration

    def create(self, request, *args, **kwargs):
        # Get building_id if provided (optional)
        building_id = request.data.get('building_id')
        
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            # Format error messages for frontend
            formatted_errors = {}
            for field, errors in serializer.errors.items():
                if isinstance(errors, list):
                    formatted_errors[field] = str(errors[0])
                else:
                    formatted_errors[field] = str(errors)
            return Response({"errors": formatted_errors}, status=status.HTTP_400_BAD_REQUEST)
            
        # Save user with building_id if provided, otherwise without it
        if building_id:
            user = serializer.save(building_id=building_id)
        else:
            user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Prepare response data
        response_data = {
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)

@method_decorator(csrf_exempt, name='dispatch')
class CustomLoginView(TokenObtainPairView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        # Get the email/username and password from request
        email = request.data.get('email')
        password = request.data.get('password')
        building_id = request.data.get('building_id')  # Optional
        
        if not email or not password:
            return Response(
                {"errors": {"email": "Email is required", "password": "Password is required"}}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to authenticate with email (since USERNAME_FIELD is email)
        user = authenticate(request, username=email, password=password)
        
        if user is None:
            return Response(
                {"errors": {"credentials": "Invalid email or password"}}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.is_active:
            return Response(
                {"errors": {"account": "Account is deactivated"}}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update user's building_id only if provided
        if building_id:
            user.building_id = building_id
            user.save(update_fields=['building_id'])
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Prepare response data
        response_data = {
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
        return Response(response_data, status=status.HTTP_200_OK)

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only users with appropriate permissions can view user list
        if self.request.user.role in ['master', 'manager']:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only users with appropriate permissions can modify other users
        if self.request.user.role in ['master', 'manager']:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)