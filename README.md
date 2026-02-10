# Cricket Utility - Cricket Club Management System

A comprehensive cricket club management API built with FastAPI, featuring match scoring, team management, and financial tracking.

## Features

- **Match Management**: Create and manage cricket matches with detailed scoring
- **Live Scoring**: Real-time ball-by-ball scoring with undo functionality
- **Team Management**: Manage teams and players
- **Financial Tracking**: Track club finances and expenses
- **Notifications**: Push notifications for match events
- **PIN-based Security**: Role-based access control with PIN authentication

## Tech Stack

- **Backend**: FastAPI with Python 3.8+
- **Database**: SQLite (with PostgreSQL support)
- **Authentication**: PIN-based role system
- **Rate Limiting**: Built-in rate limiting with slowapi
- **CORS**: Configurable CORS middleware

## Installation

1. Clone the repository:
```bash
git clone https://github.com/mudassirsami/cricketutility.git
cd cricketutility/backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Generate PIN hashes:
```bash
python generate_pin.py
```

6. Run the application:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

- `DATABASE_URL`: Database connection string
- `MANAGER_PIN_HASH`: Hashed PIN for manager role
- `SCORER_PIN_HASH`: Hashed PIN for scorer role
- `RATE_LIMIT`: Rate limit configuration (default: "30/minute")
- `VAPID_PUBLIC_KEY`: Public key for push notifications
- `VAPID_PRIVATE_KEY`: Private key for push notifications
- `VAPID_EMAIL`: Email for VAPID authentication

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection and setup
│   ├── security.py          # PIN authentication
│   ├── models/              # SQLAlchemy models
│   ├── routers/             # API route handlers
│   ├── schemas/             # Pydantic schemas
│   └── services/            # Business logic services
├── .env.example             # Environment variables template
├── generate_pin.py          # PIN hash generation utility
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## API Endpoints

### Health Check
- `GET /api/health` - Health check endpoint

### Matches
- `GET /api/matches` - List all matches
- `POST /api/matches` - Create new match (scorer PIN required)
- `GET /api/matches/{match_id}` - Get match details
- `GET /api/matches/{match_id}/scorecard` - Get full scorecard
- `POST /api/matches/{match_id}/toss` - Set toss result (scorer PIN required)
- `POST /api/matches/{match_id}/innings` - Start innings (scorer PIN required)
- `POST /api/matches/{match_id}/ball` - Record ball event (scorer PIN required)
- `POST /api/matches/{match_id}/undo` - Undo last ball (scorer PIN required)
- `POST /api/matches/{match_id}/change-bowler` - Change bowler (scorer PIN required)
- `POST /api/matches/{match_id}/swap-strike` - Swap striker (scorer PIN required)
- `POST /api/matches/{match_id}/end-innings` - End innings (scorer PIN required)
- `POST /api/matches/{match_id}/abandon` - Abandon match (scorer PIN required)
- `DELETE /api/matches/{match_id}` - Delete match (scorer PIN required)

### Upcoming Matches
- `GET /api/upcoming` - List upcoming matches
- `POST /api/upcoming` - Add upcoming match (manager PIN required)
- `PUT /api/upcoming/{match_id}` - Update upcoming match (manager PIN required)
- `DELETE /api/upcoming/{match_id}` - Delete upcoming match (manager PIN required)

### Finance
- `GET /api/finance/summary` - Get financial summary (manager PIN required)
- `GET /api/finance/transactions` - List transactions (manager PIN required)
- `POST /api/finance/transactions` - Add transaction (manager PIN required)
- `PUT /api/finance/transactions/{transaction_id}` - Update transaction (manager PIN required)
- `DELETE /api/finance/transactions/{transaction_id}` - Delete transaction (manager PIN required)

### Notifications
- `POST /api/notifications/subscribe` - Subscribe to notifications
- `POST /api/notifications/send` - Send notification (manager PIN required)

## Authentication

The API uses PIN-based authentication with two roles:

1. **Scorer**: Can create and manage matches, record scoring events
2. **Manager**: Can manage finances, upcoming matches, and send notifications

Include the PIN in the `X-PIN` header for protected endpoints.

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black app/
flake8 app/
```

## License

MIT License - see LICENSE file for details.
