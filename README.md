# Spy Cat Agency API

A Django REST API for managing spy cats and their missions.

## Quick Start

### Prerequisites
Requires Python 3.13. To have Python 3.13 locally run:
```bash
pyenv shell 3.13
```

### Clone the repository
git clone https://github.com/BegnazarAkh/spy-cat-agency/

### Change to the project directory
cd spy-cat-agency

### 1. Environment Setup
```bash
# Create and activate virtual environment
python3.13 -m venv .venv
source .venv/bin/activate

# Install required files
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Apply migrations (database schema is already defined)
python manage.py migrate
```

### 2. Run the Server
```bash
make run
```

The API will be available at `http://localhost:8000`

## API Documentation

- **Swagger UI**: `http://localhost:8000/api/docs/`
- **API Schema**: `http://localhost:8000/api/schema/`

## API Endpoints

### Spy Cats
- `GET /api/cats/` - List all spy cats
- `POST /api/cats/` - Create a new spy cat
- `GET /api/cats/{id}/` - Get spy cat details
- `PUT /api/cats/{id}/` - Update spy cat
- `PATCH /api/cats/{id}/` - Partial update spy cat
- `DELETE /api/cats/{id}/` - Delete spy cat

### Missions
- `GET /api/missions/` - List all missions
- `POST /api/missions/` - Create a new mission
- `GET /api/missions/{id}/` - Get mission details
- `PUT /api/missions/{id}/` - Update mission
- `PATCH /api/missions/{id}/` - Partial update mission
- `DELETE /api/missions/{id}/` - Delete mission
- `POST /api/missions/{id}/assign_cat/` - Assign cat to mission
- `POST /api/missions/{id}/complete/` - Mark mission as complete

## Testing the API

### Using curl

**Create a spy cat:**
```bash
curl -X POST http://localhost:8000/api/cats/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Agent Whiskers",
    "years_of_experience": 5,
    "breed": "Siamese",
    "salary": 50000
  }'
```

**List all cats:**
```bash
curl http://localhost:8000/api/cats/
```

**Create a mission:**
```bash
curl -X POST http://localhost:8000/api/missions/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Operation Tuna",
    "description": "Infiltrate the fish market",
    "targets": [
      {"name": "Fish Vendor", "country": "USA", "notes": "Suspicious activity"},
      {"name": "Market Manager", "country": "USA", "notes": "Potential accomplice"}
    ]
  }'
```

### Using Python requests
```python
import requests

# Create a spy cat
cat_data = {
    "name": "Agent Mittens",
    "years_of_experience": 3,
    "breed": "Persian",
    "salary": 45000
}
response = requests.post('http://localhost:8000/api/cats/', json=cat_data)
print(response.json())

# List missions
response = requests.get('http://localhost:8000/api/missions/')
print(response.json())
```

## Development Commands

```bash
# Install dependencies
make install

# Run tests
make test

# Run with coverage
make coverage

# Lint code
make lint

# Security check
make bandit

# Run migrations
make migrate

# Clean up
make clean

# Run all checks
make verify
```

## Project Structure

```
spy-cat-agency/
├── spy_cat_agency/     # Django project settings
├── spy_cats/           # Main app with models, views, serializers
├── requirements.txt    # Python dependencies
├── Makefile           # Development commands
├── .env.example       # Environment variables template
└── manage.py          # Django management script
```

## Environment Variables

Create a `.env` file with:
```
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Features

- RESTful API for spy cats and missions
- Automatic API documentation with Swagger
- Mission target management
- Cat assignment to missions
- Mission completion tracking
- Comprehensive test coverage
- Code quality checks (pylint, bandit)