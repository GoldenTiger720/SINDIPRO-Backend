from rest_framework import generics, status, permissions
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from auth_system.serializers import UserSerializer

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
