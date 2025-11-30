from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from auth_system.serializers import UserSerializer
from .models import BuildingAccess
from .serializers import BuildingAccessSerializer, UserBuildingAssignmentSerializer
from building_mgmt.models import Building

User = get_user_model()


class UserUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for updating and deleting users.
    Only accessible by master and manager roles.

    PUT /api/users/{id}/ - Update user details
    DELETE /api/users/{id}/ - Delete user
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Restrict access based on user role.
        Only master and manager roles can modify other users.
        """
        if self.request.user.role in ['master', 'manager']:
            return User.objects.all()
        # Regular users can only access their own data
        return User.objects.filter(id=self.request.user.id)

    def update(self, request, *args, **kwargs):
        """
        Handle PUT request to update user details.
        Validates that only authorized users can update other users.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Check permission - users can only edit themselves unless they're master/manager
        if instance.id != request.user.id and request.user.role not in ['master', 'manager']:
            return Response(
                {"errors": {"permission": "You do not have permission to edit this user."}},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if not serializer.is_valid():
            # Format error messages for frontend consistency
            formatted_errors = {}
            for field, errors in serializer.errors.items():
                if isinstance(errors, list):
                    formatted_errors[field] = str(errors[0])
                else:
                    formatted_errors[field] = str(errors)
            return Response({"errors": formatted_errors}, status=status.HTTP_400_BAD_REQUEST)

        self.perform_update(serializer)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a user.
        Only master and manager roles can delete users.
        Users cannot delete themselves.
        """
        instance = self.get_object()

        # Check permission - only master/manager can delete users
        if request.user.role not in ['master', 'manager']:
            return Response(
                {"errors": {"permission": "You do not have permission to delete users."}},
                status=status.HTTP_403_FORBIDDEN
            )

        # Prevent users from deleting themselves
        if instance.id == request.user.id:
            return Response(
                {"errors": {"permission": "You cannot delete your own account."}},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Perform the deletion
        self.perform_destroy(instance)

        return Response(
            {"message": "User deleted successfully."},
            status=status.HTTP_200_OK
        )


class UserBuildingAccessView(APIView):
    """
    API endpoint to get and set building access for a user.

    GET /api/users/{id}/buildings/ - Get list of buildings assigned to user
    PUT /api/users/{id}/buildings/ - Update buildings assigned to user
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        """Get list of buildings assigned to a user"""
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"errors": {"user": "User not found."}},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check permission - users can only see their own buildings unless they're master/manager
        if user.id != request.user.id and request.user.role not in ['master', 'manager']:
            return Response(
                {"errors": {"permission": "You do not have permission to view this user's buildings."}},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all building accesses for this user
        building_accesses = BuildingAccess.objects.filter(user=user, is_active=True).select_related('building')
        serializer = BuildingAccessSerializer(building_accesses, many=True)

        return Response({
            "user_id": user.id,
            "buildings": serializer.data
        }, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """Update buildings assigned to a user"""
        # Only master/manager can assign buildings
        if request.user.role not in ['master', 'manager']:
            return Response(
                {"errors": {"permission": "You do not have permission to assign buildings."}},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"errors": {"user": "User not found."}},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserBuildingAssignmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        building_ids = serializer.validated_data['building_ids']

        # Remove all existing building accesses for this user
        BuildingAccess.objects.filter(user=user).delete()

        # Create new building accesses
        for building_id in building_ids:
            building = Building.objects.get(pk=building_id)
            BuildingAccess.objects.create(
                user=user,
                building=building,
                access_level='full',
                is_active=True,
                granted_by=request.user
            )

        # Return updated list
        building_accesses = BuildingAccess.objects.filter(user=user, is_active=True).select_related('building')
        response_serializer = BuildingAccessSerializer(building_accesses, many=True)

        return Response({
            "user_id": user.id,
            "buildings": response_serializer.data,
            "message": "Buildings assigned successfully."
        }, status=status.HTTP_200_OK)


class CurrentUserBuildingsView(APIView):
    """
    API endpoint to get buildings accessible by the current logged-in user.

    GET /api/users/me/buildings/ - Get list of buildings for current user

    - master/manager roles: Return all buildings
    - operator role: Return only assigned buildings
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get list of buildings for the current user based on their role"""
        user = request.user

        # master and manager can see all buildings
        if user.role in ['master', 'manager']:
            buildings = Building.objects.all()
            return Response({
                "buildings": [
                    {"id": b.id, "building_name": b.building_name}
                    for b in buildings
                ]
            }, status=status.HTTP_200_OK)

        # operator and other roles: only see assigned buildings
        building_accesses = BuildingAccess.objects.filter(
            user=user,
            is_active=True
        ).select_related('building')

        return Response({
            "buildings": [
                {"id": ba.building.id, "building_name": ba.building.building_name}
                for ba in building_accesses
            ]
        }, status=status.HTTP_200_OK)
