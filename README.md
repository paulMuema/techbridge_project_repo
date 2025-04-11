# TechBridge - Tech Skills Sharing Platform

TechBridge is a web application designed to facilitate the sharing of tech skills and resources among users. It provides a platform for users to upload, share, and discover technical resources while tracking their learning progress.

## Features

### User Management
- User registration and authentication
- Profile management with customizable information
- Role-based access control (Admin, User)
- Email verification system

### Resource Management
- Upload and share technical resources
- Support for multiple file types
- Resource categorization and tagging
- Difficulty level classification
- File download tracking

### Social Features
- Resource ratings and reviews
- Like/unlike resources
- View tracking
- User activity feed
- Messaging system

### Search and Discovery
- Advanced search functionality
- Category-based filtering
- Difficulty level filtering
- Resource type filtering

### Admin Dashboard
- User management
- Resource moderation
- System settings configuration
- Database backup and maintenance
- Cache management

## Tech Stack

- **Backend**: Python Flask
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Authentication**: Flask-Login
- **File Handling**: Werkzeug
- **Search**: Flask-Whooshee
- **Caching**: Flask-Caching

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/techbridge.git
cd techbridge
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

5. Create necessary directories:
```bash
mkdir -p static/profile_pics
mkdir -p static/resources
mkdir -p backups
```

6. Set up environment variables:
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
export SECRET_KEY=your-secret-key
```

## Configuration

The application can be configured through the admin settings panel or by modifying the following environment variables:

- `SECRET_KEY`: Application secret key
- `MAX_CONTENT_LENGTH`: Maximum file upload size (default: 16MB)
- `ALLOWED_EXTENSIONS`: Comma-separated list of allowed file extensions
- `REQUIRE_EMAIL_VERIFICATION`: Enable/disable email verification
- `ALLOW_REGISTRATION`: Enable/disable new user registration
- `ENABLE_COMMENTS`: Enable/disable resource comments
- `ENABLE_RATINGS`: Enable/disable resource ratings

## Running the Application

1. Start the development server:
```bash
flask run
```

2. Access the application at `http://localhost:5000`

## Project Structure

```
techbridge/
├── app.py                  # Main application file
├── config.py              # Configuration settings
├── requirements.txt       # Project dependencies
├── static/               # Static files
│   ├── css/             # Stylesheets
│   ├── js/              # JavaScript files
│   ├── profile_pics/    # User profile pictures
│   └── resources/       # Uploaded resources
├── templates/           # HTML templates
│   ├── admin/          # Admin templates
│   ├── auth/           # Authentication templates
│   └── resources/      # Resource-related templates
└── migrations/         # Database migrations
```

## Security Features

- Password hashing using Werkzeug
- CSRF protection
- File upload validation
- Role-based access control
- Secure session management
- Input sanitization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.

## Acknowledgments

- Flask team for the amazing web framework
- Bootstrap team for the UI components
- All contributors who have helped improve this project 