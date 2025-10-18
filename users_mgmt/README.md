# User Management API

This module provides API endpoints for managing users in the SINDIPRO system.

## Endpoints

### Update User
**Endpoint:** `PUT /api/users/{id}/`

**Description:** Update user details. Only accessible by users with `master` or `manager` roles. Users can only edit their own profile unless they have elevated permissions.

**Request Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "+1234567890",
  "role": "manager",
  "is_active_user": true
}
```

**Fields:**
- `first_name` (string, optional): User's first name
- `last_name` (string, optional): User's last name
- `email` (string, required): User's email address (must be unique)
- `phone` (string, optional): User's phone number
- `role` (string, required): User's role. Options: `master`, `manager`, `field`, `readonly`
- `is_active_user` (boolean, required): Whether the user account is active

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "john.doe@example.com",
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "manager",
  "phone": "+1234567890",
  "is_active_user": true,
  "date_joined": "2024-10-17T22:00:00Z",
  "building_id": 5,
  "building_name": "Building A"
}
```

**Error Responses:**

*403 Forbidden* - User doesn't have permission to edit this user
```json
{
  "errors": {
    "permission": "You do not have permission to edit this user."
  }
}
```

*400 Bad Request* - Validation errors
```json
{
  "errors": {
    "email": "This field is required.",
    "role": "Invalid role selected."
  }
}
```

---

### Delete User
**Endpoint:** `DELETE /api/users/{id}/`

**Description:** Delete a user from the system. Only accessible by users with `master` or `manager` roles. Users cannot delete their own account.

**Request Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "message": "User deleted successfully."
}
```

**Error Responses:**

*403 Forbidden* - User doesn't have permission to delete users
```json
{
  "errors": {
    "permission": "You do not have permission to delete users."
  }
}
```

*400 Bad Request* - Attempting to delete own account
```json
{
  "errors": {
    "permission": "You cannot delete your own account."
  }
}
```

*404 Not Found* - User with given ID doesn't exist
```json
{
  "detail": "Not found."
}
```

---

## Permissions

### Role-Based Access Control

| Role | Can Update Own Profile | Can Update Other Users | Can Delete Users |
|------|------------------------|------------------------|------------------|
| master | ✅ | ✅ | ✅ |
| manager | ✅ | ✅ | ✅ |
| field | ✅ | ❌ | ❌ |
| readonly | ✅ | ❌ | ❌ |

### Business Rules

1. **Update Permissions:**
   - All users can update their own profile
   - Only `master` and `manager` roles can update other users
   - Users cannot change their own role to `master` unless they already have that role

2. **Delete Permissions:**
   - Only `master` and `manager` roles can delete users
   - Users cannot delete their own account (to prevent accidental lockout)
   - Super users should have at least one `master` account active

3. **Field Validation:**
   - Email must be unique across all users
   - Email is used as the username for authentication
   - Role must be one of: `master`, `manager`, `field`, `readonly`
   - Phone numbers can be in any format (validation is flexible)

---

## Integration with Frontend

The frontend sends requests to these endpoints using the `makeAuthenticatedRequest` utility function which automatically:
- Adds the JWT authorization token
- Sets appropriate headers
- Handles errors and formats error messages
- Adds building_id to requests when applicable

**Example Frontend Usage:**

```typescript
// Update user
await makeAuthenticatedRequest(`/api/users/${userId}/`, {
  method: 'PUT',
  body: JSON.stringify({
    first_name: 'John',
    last_name: 'Doe',
    email: 'john.doe@example.com',
    phone: '+1234567890',
    role: 'manager',
    is_active_user: true
  })
});

// Delete user
await makeAuthenticatedRequest(`/api/users/${userId}/`, {
  method: 'DELETE'
});
```

---

## Testing

To test the endpoints manually:

1. **Get an access token** by logging in:
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "your_password"}'
```

2. **Update a user:**
```bash
curl -X PUT http://localhost:8000/api/users/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Updated",
    "last_name": "Name",
    "email": "updated@example.com",
    "phone": "+1234567890",
    "role": "manager",
    "is_active_user": true
  }'
```

3. **Delete a user:**
```bash
curl -X DELETE http://localhost:8000/api/users/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Related Files

- **View:** `/var/www/sindipro/users_mgmt/views.py`
- **URL Configuration:** `/var/www/sindipro/users_mgmt/urls.py`
- **Serializer:** `/var/www/sindipro/auth_system/serializers.py`
- **Model:** `/var/www/sindipro/auth_system/models.py`
- **Frontend Component:** `/var/www/html/frontend/src/pages/Users.tsx`
