# Medical Office App Multi-User Implementation Plan

## 1. Database Migration

### 1.1 PostgreSQL Setup
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE medical_office;"
sudo -u postgres psql -c "CREATE USER app_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE medical_office TO app_user;"
```

### 1.2 Schema Migration
Convert SQLite schema to PostgreSQL:
```sql
-- patients table
CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    phone_number VARCHAR(20),
    blood_pressure_systolic INTEGER,
    blood_pressure_diastolic INTEGER,
    oxygen_saturation INTEGER,
    heart_rate INTEGER,
    first_seen_date TIMESTAMP NOT NULL
);

-- Add triggers for change notifications
CREATE OR REPLACE FUNCTION notify_change() RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('data_changes', TG_TABLE_NAME || ',' || NEW.patient_id::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER patients_notify
AFTER INSERT OR UPDATE ON patients
FOR EACH ROW EXECUTE FUNCTION notify_change();
```

## 2. API Server Implementation

### 2.1 FastAPI Setup
```python
# requirements.txt
fastapi==0.68.1
uvicorn==0.15.0
websockets==10.1
python-multipart==0.0.5
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
psycopg2-binary==2.9.3
```

### 2.2 WebSocket Endpoint
```python
from fastapi import WebSocket
from databases import Database

database = Database("postgresql://app_user:secure_password@localhost/medical_office")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    async with database.connection() as connection:
        await connection.execute("LISTEN data_changes")
        while True:
            notification = await connection.connection.notifies.get()
            await websocket.send_text(notification.payload)
```

## 3. Client Modifications

### 3.1 API Client Class
```python
import requests
from websockets import connect

class MedicalOfficeAPI:
    def __init__(self):
        self.base_url = "http://server:8000"
        self.ws_url = "ws://server:8000/ws"
        self.token = None
    
    async def listen_for_changes(self, callback):
        async with connect(self.ws_url) as websocket:
            while True:
                message = await websocket.recv()
                table, record_id = message.split(',')
                callback(table, record_id)
```

## 4. Security Implementation

### 4.1 JWT Authentication Flow
```python
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "secret-key-here"
ALGORITHM = "HS256"

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
```

## 5. Deployment

### 5.1 Docker Compose
```yaml
version: '3.8'

services:
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: medical_office
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  api:
    build: .
    command: uvicorn main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    depends_on:
      - db

volumes:
  pgdata:
```

## 6. Rollback Plan

1. Maintain SQLite database as fallback during transition
2. Create daily backups during migration period
3. Feature flag system for new API endpoints
4. Monitor with:
```bash
watch -n 1 "curl -s http://localhost:8000/health | jq"
```

Would you like me to create this document in the project's docs directory?