# PostgreSQL + PgAdmin Setup Guide

## ✅ Current Status
- PostgreSQL is running and connected
- Database tables created: `users`, `items`
- FastAPI configured to use PostgreSQL

## 📋 Next Steps

### 1. **Restart FastAPI Server**
Kill the current server and restart with PostgreSQL:
```bash
# In Terminal (Ctrl+C to stop current server)
cd /home/mostafa/fastapi_app/fastapi_app
source venv/bin/activate
uvicorn App.main:app --reload
```

### 2. **Test with Swagger**
Open your browser:
```
http://127.0.0.1:8000/docs
```

Then test:
1. **POST /users/** - Create a user
2. **POST /users/login** - Get JWT token
3. **GET /users/{id}** - Access with token

### 3. **Access PgAdmin**

#### Option A: Install PgAdmin Locally
```bash
# Install pgadmin4
pip install pgadmin4

# Run pgadmin4
pgadmin4
```
Open: http://localhost:5050

#### Option B: Use Docker PgAdmin
```bash
docker run -p 5050:80 \
  -e PGADMIN_DEFAULT_EMAIL=admin@example.com \
  -e PGADMIN_DEFAULT_PASSWORD=admin \
  dpage/pgadmin4
```
Open: http://localhost:5050

#### Option C: Use Online PgAdmin
Use DBeaver (free GUI):
```bash
# Download from: https://dbeaver.io/download/
```

### 4. **Connect PgAdmin to Your Database**

In PgAdmin:
1. **Register Server**
2. **Connection Details:**
   - Host: `localhost`
   - Port: `5432`
   - Username: `admin`
   - Password: `admin`
   - Database: `postgres`

### 5. **Database Connection String**
```
postgresql://admin:admin@localhost:5432/postgres
```

### 6. **Quick Test Commands**

Create user:
```bash
curl -X POST http://127.0.0.1:8000/users/ \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "ahmed",
  "age": 20,
  "email": "test@example.com",
  "password": "pass123"
}'
```

Query database directly:
```bash
psql -U admin -h localhost -d postgres -c "SELECT * FROM users;"
```

## 🔗 Useful Links
- PostgreSQL: http://localhost:5432
- FastAPI Docs: http://127.0.0.1:8000/docs
- FastAPI ReDoc: http://127.0.0.1:8000/redoc
- Health Check: http://127.0.0.1:8000/health

## ⚙️ Environment Variables (.env)
```
DATABASE_URL=postgresql://admin:admin@localhost:5432/postgres
```

## 🐛 Troubleshooting

**Connection refused?**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Start PostgreSQL
sudo systemctl start postgresql
```

**Wrong credentials?**
```bash
# Reset PostgreSQL password
sudo sudo -u postgres psql -c "ALTER USER admin WITH PASSWORD 'admin';"
```

**View all tables**
```bash
psql -U admin -h localhost -d postgres -c "\dt"
```
