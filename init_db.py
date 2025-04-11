from app import app, db, User, Resource, Message
from werkzeug.security import generate_password_hash
from datetime import datetime

def init_db():
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        
        # Create default admin user if not exists
        if not User.query.filter_by(email='admin@techbridge.com').first():
            admin = User(
                name='Admin',
                email='admin@techbridge.com',
                password=generate_password_hash('admin123'),
                role='admin',
                profile_pic='default_profile.svg'
            )
            db.session.add(admin)
            db.session.commit()

            # Create a sample resource
            resource = Resource(
                title='Getting Started with TechBridge',
                description='Welcome to TechBridge! This guide will help you get started with sharing and discovering tech resources.',
                difficulty_level='beginner',
                resource_type='tutorial',
                category='general',
                tags='getting started,guide,tutorial',
                user_id=admin.id
            )
            db.session.add(resource)
            db.session.commit()

            # Create a sample message
            message = Message(
                sender_id=admin.id,
                recipient_id=admin.id,
                subject='Welcome to TechBridge!',
                body='Welcome to TechBridge! This is a sample message to demonstrate the messaging system.',
                read=False
            )
            db.session.add(message)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
