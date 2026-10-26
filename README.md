# CalendarApp

A calendar application for managing events, invites, and voting on event proposals.

## Features

- User authentication and registration
- Create and manage calendar events
- Send event invites
- Vote on event proposals
- Real-time updates (if applicable)

## Tech Stack

- **Backend**: Django, Django REST Framework
- **Frontend**: React
- **Database**: SQLite (default)

## Setup

### Backend
1. Navigate to `backend/`
2. Create and activate a virtual environment: `python -m venv venv`, then `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (macOS/Linux)
3. Install dependencies: `pip install -r requirements.txt` (or `requirements-dev.txt` to include the test tools)
4. Run migrations: `python manage.py migrate`
5. Start server: `python manage.py runserver`

### Frontend
1. Navigate to `frontend/`
2. Install dependencies: `npm install`
3. Start development server: `npm start`

## Usage

- Register/Login to access the app
- Create events and send invites
- Vote on proposed events

## Contributing

Feel free to submit issues and pull requests.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.