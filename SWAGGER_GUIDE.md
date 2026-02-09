# FastAPI Swagger Testing Guide

## URLs
- **Swagger UI**: http://127.0.0.1:8000/docs
- **Alternative Docs**: http://127.0.0.1:8000/redoc
- **OpenAPI JSON**: http://127.0.0.1:8000/openapi.json

## Available Endpoints

### Public Endpoints (No Auth Required)
- **POST /users/** - Create new user
  - Request: `{name, age, email, password}`
  - Response: `{id, name, age, email}`

- **POST /users/login** - Login to get JWT token
  - Request: `{email, password}`
  - Response: `{access_token, token_type}`

### Protected Endpoints (JWT Required)
- **GET /users/{user_id}** - Get user details
- **PUT /users/{user_id}** - Update user
- **DELETE /users/{user_id}** - Delete user

### Item Endpoints
- **POST /items/** - Create item
- **GET /items/{item_id}** - Get item
- **GET /items/user/{user_id}** - Get user's items

## Testing Flow

1. **Create User**: POST /users/
   ```json
   {
     "name": "John Doe",
     "age": 30,
     "email": "john@example.com",
     "password": "password123"
   }
   ```

2. **Login**: POST /users/login
   ```json
   {
     "email": "john@example.com",
     "password": "password123"
   }
   ```
   → Copy the `access_token`

3. **Authorize**: Click Lock icon → Paste token

4. **Test Protected**: GET /users/{user_id}
   → You'll now have access

## Database
- **Type**: SQLite
- **Location**: `test.db`
- **Tables**: users, items
