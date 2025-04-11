from app import app, db, User, Resource, ResourceFile
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_defaults():
    with app.app_context():
        # Create default admin user if not exists
        if not User.query.filter_by(email='admin@techbridge.com').first():
            admin = User(
                name='Admin',
                email='admin@techbridge.com',
                password=generate_password_hash('admin123'),
                profile_pic='default.jpg'
            )
            db.session.add(admin)
            db.session.commit()

            # Create default resources
            resources = [
                {
                    'title': 'Python Programming Guide for Beginners',
                    'description': 'A comprehensive guide to Python programming language covering basic concepts, data structures, and best practices. Perfect for those starting their programming journey.',
                    'difficulty_level': 'beginner',
                    'resource_type': 'tutorial',
                    'tags': 'python,programming,beginner',
                    'user_id': admin.id,
                    'views': 125,
                    'likes': 45
                },
                {
                    'title': 'Web Development Tools and Extensions',
                    'description': 'Collection of essential tools, browser extensions, and VS Code plugins that every web developer should know about. Boost your productivity with these carefully selected resources.',
                    'difficulty_level': 'intermediate',
                    'resource_type': 'tool',
                    'tags': 'web development,tools,productivity',
                    'user_id': admin.id,
                    'views': 89,
                    'likes': 32
                },
                {
                    'title': 'Advanced React Design Patterns',
                    'description': 'Deep dive into advanced React patterns including HOCs, Render Props, Custom Hooks, and State Management. Learn how to write clean, reusable React components.',
                    'difficulty_level': 'advanced',
                    'resource_type': 'article',
                    'tags': 'react,javascript,advanced',
                    'user_id': admin.id,
                    'views': 67,
                    'likes': 28
                },
                {
                    'title': 'Building RESTful APIs with Flask',
                    'description': 'Learn how to build scalable RESTful APIs using Flask framework. Covers routing, authentication, database integration, and best practices for API design.',
                    'difficulty_level': 'intermediate',
                    'resource_type': 'project',
                    'tags': 'flask,python,api,backend',
                    'user_id': admin.id,
                    'views': 156,
                    'likes': 52
                }
            ]

            for resource_data in resources:
                resource = Resource(**resource_data)
                db.session.add(resource)
            
            db.session.commit()
            print("Default content created successfully!")

if __name__ == '__main__':
    create_defaults()
