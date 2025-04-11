import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy.sql import func
from flask_migrate import Migrate
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///techbridge.db'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'profile_pics')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['RESOURCE_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'resources')

# Ensure resource folder exists
os.makedirs(app.config['RESOURCE_FOLDER'], exist_ok=True)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_RESOURCE_EXTENSIONS = {
    'document': {'pdf', 'doc', 'docx', 'txt', 'md'},
    'image': {'png', 'jpg', 'jpeg', 'gif'},
    'video': {'mp4', 'webm', 'mov'},
    'code': {'py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'rb'}
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_default_profile_pic():
    return 'default_profile.svg'

def allowed_resource_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {
        ext for exts in ALLOWED_RESOURCE_EXTENSIONS.values() for ext in exts
    }

def get_file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    for file_type, extensions in ALLOWED_RESOURCE_EXTENSIONS.items():
        if ext in extensions:
            return file_type
    return None

class ResourceFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer)  # Size in bytes
    description = db.Column(db.Text)
    download_count = db.Column(db.Integer, default=0)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    difficulty_level = db.Column(db.String(20), nullable=False, default='beginner')
    resource_type = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='general')
    tags = db.Column(db.String(500))
    external_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='resources')
    files = db.relationship('ResourceFile', backref='resource', lazy=True, cascade='all, delete-orphan')
    likes = db.Column(db.Integer, default=0)
    content_type = db.Column(db.String(50))  # 'url', 'file', or 'code'
    _rating = db.Column('rating', db.Float, default=0.0)
    _rating_count = db.Column('rating_count', db.Integer, default=0)
    liked_by = db.relationship('User', secondary='resource_likes', backref=db.backref('liked_resources', lazy='dynamic'))

    @property
    def rating(self):
        return self._rating or 0.0

    @property
    def rating_count(self):
        return self._rating_count or 0

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    profile_pic = db.Column(db.String(200), default=get_default_profile_pic)
    
    # Profile fields
    profession = db.Column(db.String(100))
    company = db.Column(db.String(100))
    location = db.Column(db.String(100))
    bio = db.Column(db.Text)
    website = db.Column(db.String(200))
    github = db.Column(db.String(100))
    linkedin = db.Column(db.String(100))
    skills = db.Column(db.Text)  # Stored as comma-separated values
    interests = db.Column(db.Text)  # Stored as comma-separated values
    experience_level = db.Column(db.String(20))  # e.g., 'Beginner', 'Intermediate', 'Advanced'
    preferred_languages = db.Column(db.Text)  # Stored as comma-separated values
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def unread_messages_count(self):
        return Message.query.filter_by(recipient_id=self.id, read=False).count()

# New association table for resource likes
resource_likes = db.Table('resource_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('resource_id', db.Integer, db.ForeignKey('resource.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

# Create a new table for resource ratings
resource_ratings = db.Table('resource_ratings',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('resource_id', db.Integer, db.ForeignKey('resource.id'), primary_key=True),
    db.Column('rating', db.Integer, nullable=False),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(200))
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('login'))

        login_user(user, remember=remember)
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')

        if not all([email, name, password, confirm_password, role]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists.', 'danger')
            return redirect(url_for('register'))

        new_user = User(
            email=email,
            name=name,
            password=generate_password_hash(password, method='sha256'),
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    stats = {
        'total_resources': Resource.query.count(),
        'total_files': ResourceFile.query.count(),
        'my_resources': Resource.query.filter_by(user_id=current_user.id).count()
    }
    
    # Get user's resources
    my_resources = Resource.query.filter_by(user_id=current_user.id).order_by(Resource.created_at.desc()).all()
    
    # Get recent activity
    recent_resources = Resource.query.order_by(Resource.created_at.desc()).limit(5).all()
    recent_activity = []
    
    for resource in recent_resources:
        activity = {
            'type': 'primary' if resource.user_id == current_user.id else 'success',
            'icon': 'file-earmark-plus' if resource.user_id == current_user.id else 'file-earmark-text',
            'title': 'You shared a resource' if resource.user_id == current_user.id else f'{resource.user.name} shared a resource',
            'description': f'A new {resource.resource_type} resource was shared',
            'time': resource.created_at.strftime('%Y-%m-%d %H:%M'),
            'resource': {
                'id': resource.id,
                'title': resource.title,
                'description': resource.description,
                'icon': {
                    'tutorial': 'book',
                    'article': 'file-text',
                    'video': 'play-circle',
                    'code': 'code-square',
                    'tool': 'tools',
                    'other': 'file-earmark'
                }.get(resource.resource_type, 'file-earmark'),
                'files': resource.files
            }
        }
        recent_activity.append(activity)
    
    return render_template('dashboard.html', stats=stats, my_resources=my_resources, recent_activity=recent_activity)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/profile/<username>')
def view_profile(username):
    user = User.query.filter_by(name=username).first_or_404()
    resources = Resource.query.filter_by(user_id=user.id).order_by(Resource.created_at.desc()).all()
    
    # Get user's skills and interests as lists
    skills = user.skills.split(',') if user.skills else []
    interests = user.interests.split(',') if user.interests else []
    preferred_languages = user.preferred_languages.split(',') if user.preferred_languages else []
    
    return render_template('view_profile.html', 
                         user=user, 
                         resources=resources,
                         skills=skills,
                         interests=interests,
                         preferred_languages=preferred_languages)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # Handle profile picture upload
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename and allowed_file(file.filename):
                # Create unique filename with timestamp
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                
                # Delete old profile picture if it exists and isn't the default
                if current_user.profile_pic and current_user.profile_pic != get_default_profile_pic():
                    old_pic_path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_pic)
                    if os.path.exists(old_pic_path):
                        os.remove(old_pic_path)
                
                # Save new profile picture
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                current_user.profile_pic = filename
        # Update user profile
        current_user.profession = request.form.get('profession')
        current_user.company = request.form.get('company')
        current_user.location = request.form.get('location')
        current_user.bio = request.form.get('bio')
        current_user.website = request.form.get('website')
        current_user.github = request.form.get('github')
        current_user.linkedin = request.form.get('linkedin')
        current_user.skills = ','.join(request.form.getlist('skills[]'))
        current_user.interests = ','.join(request.form.getlist('interests[]'))
        current_user.experience_level = request.form.get('experience_level')
        current_user.preferred_languages = ','.join(request.form.getlist('preferred_languages[]'))
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/resources')
def resources():
    # Get filter type from query parameters
    resource_type = request.args.get('type', 'all')
    
    # Query resources with optional type filter
    if resource_type and resource_type != 'all':
        resources = Resource.query.filter_by(resource_type=resource_type).order_by(Resource.created_at.desc()).all()
    else:
        resources = Resource.query.order_by(Resource.created_at.desc()).all()
    
    return render_template('resources.html', resources=resources, current_type=resource_type)

@app.route('/new_resource', methods=['GET', 'POST'])
@login_required
def new_resource():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        difficulty_level = request.form.get('difficulty_level')
        resource_type = request.form.get('resource_type')
        category = request.form.get('category', 'general')
        tags = request.form.get('tags')
        content_type = request.form.get('content_type')
        external_url = request.form.get('url')

        # Create new resource
        resource = Resource(
            title=title,
            description=description,
            difficulty_level=difficulty_level,
            resource_type=resource_type,
            category=category,
            tags=tags,
            content_type=content_type,
            external_url=external_url,
            user_id=current_user.id
        )
        db.session.add(resource)
        db.session.commit()

        # Handle file uploads
        if 'files' in request.files:
            files = request.files.getlist('files')
            print(f"Number of files received: {len(files)}")  # Debug log
            
            for file in files:
                if file and file.filename and allowed_resource_file(file.filename):
                    print(f"Processing file: {file.filename}")  # Debug log
                    
                    # Generate unique filename
                    original_filename = secure_filename(file.filename)
                    filename = f"{uuid.uuid4()}_{original_filename}"
                    file_path = os.path.join(app.config['RESOURCE_FOLDER'], filename)
                    
                    print(f"Saving file to: {file_path}")  # Debug log
                    file.save(file_path)
                    
                    # Verify file was saved
                    if os.path.exists(file_path):
                        print(f"File saved successfully: {file_path}")  # Debug log
                    else:
                        print(f"Error: File not saved to {file_path}")  # Debug log
                    
                    # Get file size
                    file_size = os.path.getsize(file_path)
                    file_type = get_file_type(original_filename)
                    
                    # Create resource file record
                    resource_file = ResourceFile(
                        filename=filename,
                        original_filename=original_filename,
                        file_type=file_type,
                        file_size=file_size,
                        resource_id=resource.id
                    )
                    db.session.add(resource_file)
                    print(f"Created ResourceFile record for: {filename}")  # Debug log
            
            try:
                db.session.commit()
                print("Successfully committed file records to database")  # Debug log
            except Exception as e:
                print(f"Error committing to database: {str(e)}")  # Debug log
                db.session.rollback()

        flash('Resource created successfully!', 'success')
        return redirect(url_for('resources'))

    return render_template('new_resource.html')

@app.route('/resource/<int:id>')
def view_resource(id):
    resource = Resource.query.get_or_404(id)
    
    # Check if current user has liked the resource
    is_liked = False
    if current_user.is_authenticated:
        is_liked = current_user in resource.liked_by
    
    return render_template('view_resource.html',
                         resource=resource,
                         is_liked=is_liked)

@app.route('/resources/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_resource(id):
    resource = Resource.query.get_or_404(id)
    
    # Check if the current user is the owner
    if resource.user_id != current_user.id:
        flash('You do not have permission to edit this resource.', 'danger')
        return redirect(url_for('resources'))
    
    if request.method == 'POST':
        resource.title = request.form.get('title')
        resource.description = request.form.get('description')
        resource.resource_type = request.form.get('type')
        resource.difficulty_level = request.form.get('difficulty')
        resource.tags = request.form.get('tags')
        
        # Handle file updates
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                # Delete old file if it exists
                if resource.files:
                    old_file = resource.files[0]
                    try:
                        os.remove(os.path.join(app.config['RESOURCE_FOLDER'], old_file.filename))
                        db.session.delete(old_file)
                    except Exception as e:
                        app.logger.error(f'Error deleting file: {e}')
                
                # Save new file
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['RESOURCE_FOLDER'], filename))
                new_file = ResourceFile(filename=filename, resource_id=resource.id)
                db.session.add(new_file)
        
        db.session.commit()
        flash('Resource updated successfully!', 'success')
        return redirect(url_for('view_resource', id=resource.id))
    
    return render_template('edit_resource.html', resource=resource)

@app.route('/resources/<int:id>/delete', methods=['POST'])
@login_required
def delete_resource(id):
    resource = Resource.query.get_or_404(id)
    
    # Check if the current user is the owner of the resource
    if current_user.id != resource.user_id:
        flash('You are not authorized to delete this resource.', 'danger')
        return redirect(url_for('view_resource', id=id))
    
    try:
        # Delete associated files
        for file in resource.files:
            file_path = os.path.join(app.config['RESOURCE_FOLDER'], file.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Delete the resource from database
        db.session.delete(resource)
        db.session.commit()
        flash('Resource deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the resource.', 'danger')
        app.logger.error(f'Error deleting resource: {str(e)}')
    
    return redirect(url_for('dashboard'))

@app.route('/resources/<int:id>/file/<filename>')
@login_required
def resource_file(id, filename):
    """Download a resource file"""
    resource = Resource.query.get_or_404(id)
    
    # Check if the resource has any files
    if not resource.files:
        flash('No file available for this resource', 'error')
        return redirect(url_for('view_resource', id=id))
    
    # Find the specific file
    resource_file = next((f for f in resource.files if f.filename == filename), None)
    if not resource_file:
        flash('File not found', 'error')
        return redirect(url_for('view_resource', id=id))
    
    # Increment download count
    resource_file.download_count += 1
    db.session.commit()
    
    # Send the file
    return send_from_directory(
        app.config['RESOURCE_FOLDER'],
        resource_file.filename,
        as_attachment=True,
        download_name=resource_file.original_filename
    )

@app.route('/my-resources')
@login_required
def my_resources():
    resources = Resource.query.filter_by(user_id=current_user.id).order_by(Resource.created_at.desc()).all()
    return render_template('my_resources.html', resources=resources)

# Copy default profile picture to upload folder
def setup_defaults():
    default_pic_source = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images', get_default_profile_pic())
    default_pic_dest = os.path.join(app.config['UPLOAD_FOLDER'], get_default_profile_pic())
    
    if not os.path.exists(default_pic_dest) and os.path.exists(default_pic_source):
        from shutil import copy2
        copy2(default_pic_source, default_pic_dest)

# Set up Flask-SQLAlchemy
with app.app_context():
    db.create_all()
    setup_defaults()

# New routes for resource interaction
@app.route('/resources/<int:id>/like', methods=['POST'])
@login_required
def like_resource(id):
    resource = Resource.query.get_or_404(id)
    if current_user in resource.liked_by:
        resource.liked_by.remove(current_user)
        resource.likes -= 1
        action = 'unliked'
    else:
        resource.liked_by.append(current_user)
        resource.likes += 1
        action = 'liked'
    db.session.commit()
    return jsonify({'status': 'success', 'action': action, 'likes': resource.likes})

@app.route('/resources/search')
def search_resources():
    query = request.args.get('q', '')
    category = request.args.get('category', 'all')
    difficulty = request.args.get('difficulty', 'all')
    resource_type = request.args.get('type', 'all')
    
    # Base query
    resources_query = Resource.query
    
    # Apply filters
    if query:
        resources_query = resources_query.filter(
            (Resource.title.ilike(f'%{query}%')) |
            (Resource.description.ilike(f'%{query}%')) |
            (Resource.tags.ilike(f'%{query}%'))
        )
    
    if category != 'all':
        resources_query = resources_query.filter_by(category=category)
    
    if difficulty != 'all':
        resources_query = resources_query.filter_by(difficulty_level=difficulty)
    
    if resource_type != 'all':
        resources_query = resources_query.filter_by(resource_type=resource_type)
    
    # Get unique categories for filter dropdown
    categories = db.session.query(Resource.category.distinct()).all()
    categories = [cat[0] for cat in categories]
    
    resources = resources_query.order_by(Resource.created_at.desc()).all()
    
    return render_template('resources.html',
                         resources=resources,
                         query=query,
                         current_category=category,
                         current_difficulty=difficulty,
                         current_type=resource_type,
                         categories=categories)

@app.route('/resources/<int:id>/rate', methods=['POST'])
@login_required
def rate_resource(id):
    resource = Resource.query.get_or_404(id)
    rating = request.json.get('rating')
    
    if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'error': 'Invalid rating'}), 400
    
    # Check if user has already rated this resource
    existing_rating = db.session.query(resource_ratings).filter_by(
        user_id=current_user.id,
        resource_id=resource.id
    ).first()
    
    if existing_rating:
        # Update existing rating
        db.session.execute(
            resource_ratings.update()
            .where(resource_ratings.c.user_id == current_user.id)
            .where(resource_ratings.c.resource_id == resource.id)
            .values(rating=rating)
        )
    else:
        # Add new rating
        db.session.execute(
            resource_ratings.insert().values(
                user_id=current_user.id,
                resource_id=resource.id,
                rating=rating
            )
        )
        resource._rating_count = (resource._rating_count or 0) + 1
    
    # Calculate new average rating
    ratings = db.session.query(resource_ratings.c.rating).filter_by(resource_id=resource.id).all()
    total_rating = sum(r[0] for r in ratings)
    resource._rating = total_rating / len(ratings)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'rating': resource.rating,
        'rating_count': resource.rating_count
    })

@app.route('/resources/<int:id>/rating', methods=['GET'])
def get_resource_rating(id):
    resource = Resource.query.get_or_404(id)
    user_rating = None
    
    if current_user.is_authenticated:
        user_rating = db.session.query(resource_ratings.c.rating).filter_by(
            user_id=current_user.id,
            resource_id=resource.id
        ).scalar()
    
    return jsonify({
        'rating': resource.rating,
        'rating_count': resource.rating_count,
        'user_rating': user_rating
    })

def update_existing_ratings():
    """Update existing resources with default rating values"""
    with app.app_context():
        resources = Resource.query.all()
        for resource in resources:
            if resource._rating is None:
                resource._rating = 0.0
            if resource._rating_count is None:
                resource._rating_count = 0
        db.session.commit()

@app.route('/messages')
@app.route('/messages/<folder>')
@login_required
def messages(folder='inbox'):
    if folder == 'sent':
        messages = Message.query.filter_by(sender_id=current_user.id)\
                              .order_by(Message.created_at.desc()).all()
    else:
        messages = Message.query.filter_by(recipient_id=current_user.id)\
                              .order_by(Message.created_at.desc()).all()
    
    users = User.query.filter(User.id != current_user.id).all()
    unread_count = Message.query.filter_by(recipient_id=current_user.id, read=False).count()
    
    return render_template('messages.html',
                         messages=messages,
                         folder=folder,
                         users=users,
                         unread_count=unread_count)

@app.route('/messages/view/<int:message_id>')
@login_required
def view_message(message_id):
    message = Message.query.get_or_404(message_id)
    
    # Check if user has permission to view this message
    if message.recipient_id != current_user.id and message.sender_id != current_user.id:
        flash('You do not have permission to view this message.', 'danger')
        return redirect(url_for('messages'))
    
    # Mark message as read if recipient is viewing it
    if message.recipient_id == current_user.id and not message.read:
        message.read = True
        db.session.commit()
    
    folder = 'sent' if message.sender_id == current_user.id else 'inbox'
    return render_template('view_message.html', message=message, folder=folder)

@app.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    recipient_id = request.form.get('recipient_id')
    subject = request.form.get('subject')
    body = request.form.get('body')
    
    if not all([recipient_id, subject, body]):
        flash('All fields are required.', 'danger')
        return redirect(url_for('messages'))
    
    message = Message(
        sender_id=current_user.id,
        recipient_id=recipient_id,
        subject=subject,
        body=body
    )
    
    db.session.add(message)
    db.session.commit()
    
    flash('Message sent successfully!', 'success')
    return redirect(url_for('messages', folder='sent'))

# Call this function after the app is created
if __name__ == '__main__':
    update_existing_ratings()
    app.run(debug=True)
