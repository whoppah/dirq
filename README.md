# Dixa Workflow API

FastAPI backend that replicates the n8n Dixa automation workflow for processing conversation messages and generating AI responses.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy environment variables:
```bash
cp .env.example .env
```

3. Update `.env` with your API keys

4. Run the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

- `main.py` - FastAPI application entry point
- `config.py` - Configuration and environment variables
- `models.py` - Pydantic models for request/response validation
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template