from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import db, User, Project, Category, Skill, Experience, Article, Comment, Contact
from werkzeug.utils import secure_filename
from slugify import slugify
import os
import time
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')  # For local development with Neon Local Connect
load_dotenv()  # Fallback to .env

app = Flask(__name__)

# CORS Configuration - Update with your production domain
allowed_origins = os.environ.get('ALLOWED_ORIGINS', 'http://localhost,http://localhost:80').split(',')
CORS(app, origins=allowed_origins, supports_credentials=True)

# Konfigurasi
database_url = os.environ.get('DATABASE_URL')
# Fix for Railway/Render (postgres:// to postgresql://)
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'change-this-in-production-please')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', '/app/uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB max

# Pastikan folder upload ada
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
jwt = JWTManager(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Inisialisasi database dengan retry logic
def init_db():
    max_retries = 5
    retry_count = 0
    while retry_count < max_retries:
        try:
            with app.app_context():
                db.create_all()
                
                # Create default admin user if not exists
                admin = User.query.filter_by(username='admin').first()
                if not admin:
                    admin = User(username='admin', email='admin@portfolio.com', is_admin=True)
                    admin.set_password('admin123')
                    db.session.add(admin)
                
                # Create default categories
                categories_data = [
                    {'name': 'Web Development', 'icon': '🌐'},
                    {'name': 'Mobile App', 'icon': '📱'},
                    {'name': 'Machine Learning', 'icon': '🤖'},
                    {'name': 'DevOps', 'icon': '⚙️'},
                    {'name': 'Design', 'icon': '🎨'},
                    {'name': 'Other', 'icon': '📦'}
                ]
                
                for cat_data in categories_data:
                    if not Category.query.filter_by(name=cat_data['name']).first():
                        category = Category(**cat_data)
                        db.session.add(category)
                
                db.session.commit()
                print("Database initialized successfully!")
            break
        except Exception as e:
            retry_count += 1
            print(f"Database connection attempt {retry_count}/{max_retries} failed: {e}")
            if retry_count < max_retries:
                time.sleep(2)
            else:
                print("Failed to connect to database after maximum retries")

init_db()

# ============= AUTHENTICATION ROUTES =============

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists"}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already exists"}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        is_admin=data.get('is_admin', False)
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify({
            "access_token": access_token,
            "user": user.to_json()
        }), 200
    
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return jsonify(user.to_json())

# ============= PROJECT ROUTES =============

@app.route('/api/projects', methods=['GET'])
def get_projects():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'created_at')
    featured = request.args.get('featured', type=bool)
    
    query = Project.query
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(
            (Project.title.ilike(f'%{search}%')) | 
            (Project.description.ilike(f'%{search}%'))
        )
    
    if featured:
        query = query.filter_by(featured=True)
    
    # Sorting
    if sort_by == 'views':
        query = query.order_by(Project.views.desc())
    elif sort_by == 'likes':
        query = query.order_by(Project.likes.desc())
    elif sort_by == 'title':
        query = query.order_by(Project.title)
    else:
        query = query.order_by(Project.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'projects': [p.to_json() for p in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })

@app.route('/api/projects/<int:id>', methods=['GET'])
def get_project(id):
    project = Project.query.get_or_404(id)
    
    # Increment views
    project.views += 1
    db.session.commit()
    
    return jsonify(project.to_json())

@app.route('/api/projects', methods=['POST'])
def add_project():
    data = request.json
    
    new_project = Project(
        title=data['title'],
        description=data['description'],
        long_description=data.get('long_description'),
        image_url=data['image'],
        demo_url=data.get('demo_url'),
        github_url=data.get('github_url'),
        category_id=data.get('category_id'),
        tags=data.get('tags', ''),
        featured=data.get('featured', False)
    )
    
    db.session.add(new_project)
    db.session.commit()
    
    return jsonify({"message": "Project created", "project": new_project.to_json()}), 201

@app.route('/api/projects/<int:id>', methods=['PUT'])
def update_project(id):
    project = Project.query.get_or_404(id)
    data = request.json
    
    project.title = data.get('title', project.title)
    project.description = data.get('description', project.description)
    project.long_description = data.get('long_description', project.long_description)
    project.image_url = data.get('image', project.image_url)
    project.demo_url = data.get('demo_url', project.demo_url)
    project.github_url = data.get('github_url', project.github_url)
    project.category_id = data.get('category_id', project.category_id)
    project.tags = data.get('tags', project.tags)
    project.featured = data.get('featured', project.featured)
    
    db.session.commit()
    
    return jsonify({"message": "Project updated", "project": project.to_json()})

@app.route('/api/projects/<int:id>', methods=['DELETE'])
def delete_project(id):
    project = Project.query.get_or_404(id)
    db.session.delete(project)
    db.session.commit()
    
    return jsonify({"message": "Project deleted"})

@app.route('/api/projects/<int:id>/like', methods=['POST'])
def like_project(id):
    project = Project.query.get_or_404(id)
    project.likes += 1
    db.session.commit()
    
    return jsonify({"likes": project.likes})

# ============= CATEGORY ROUTES =============

@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([c.to_json() for c in categories])

@app.route('/api/categories', methods=['POST'])
def add_category():
    data = request.json
    category = Category(name=data['name'], icon=data.get('icon'))
    db.session.add(category)
    db.session.commit()
    return jsonify(category.to_json()), 201

# ============= SKILL ROUTES =============

@app.route('/api/skills', methods=['GET'])
def get_skills():
    category = request.args.get('category')
    query = Skill.query
    
    if category:
        query = query.filter_by(category=category)
    
    skills = query.all()
    return jsonify([s.to_json() for s in skills])

@app.route('/api/skills', methods=['POST'])
def add_skill():
    data = request.json
    skill = Skill(
        name=data['name'],
        level=data.get('level', 50),
        icon=data.get('icon'),
        category=data.get('category')
    )
    db.session.add(skill)
    db.session.commit()
    return jsonify(skill.to_json()), 201

@app.route('/api/skills/<int:id>', methods=['DELETE'])
def delete_skill(id):
    skill = Skill.query.get_or_404(id)
    db.session.delete(skill)
    db.session.commit()
    return jsonify({"message": "Skill deleted"})

# ============= EXPERIENCE ROUTES =============

@app.route('/api/experiences', methods=['GET'])
def get_experiences():
    experiences = Experience.query.order_by(Experience.start_date.desc()).all()
    return jsonify([e.to_json() for e in experiences])

@app.route('/api/experiences', methods=['POST'])
def add_experience():
    data = request.json
    experience = Experience(
        title=data['title'],
        company=data['company'],
        location=data.get('location'),
        start_date=data['start_date'],
        end_date=data.get('end_date'),
        description=data.get('description'),
        current=data.get('current', False)
    )
    db.session.add(experience)
    db.session.commit()
    return jsonify(experience.to_json()), 201

@app.route('/api/experiences/<int:id>', methods=['DELETE'])
def delete_experience(id):
    experience = Experience.query.get_or_404(id)
    db.session.delete(experience)
    db.session.commit()
    return jsonify({"message": "Experience deleted"})

# ============= ARTICLE/BLOG ROUTES =============

@app.route('/api/articles', methods=['GET'])
def get_articles():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 6, type=int)
    published_only = request.args.get('published', True, type=bool)
    
    query = Article.query
    if published_only:
        query = query.filter_by(published=True)
    
    query = query.order_by(Article.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'articles': [a.to_json() for a in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@app.route('/api/articles/<slug>', methods=['GET'])
def get_article(slug):
    article = Article.query.filter_by(slug=slug).first_or_404()
    article.views += 1
    db.session.commit()
    return jsonify(article.to_json())

@app.route('/api/articles', methods=['POST'])
def create_article():
    data = request.json
    slug = slugify(data['title'])
    
    article = Article(
        title=data['title'],
        slug=slug,
        content=data['content'],
        excerpt=data.get('excerpt'),
        cover_image=data.get('cover_image'),
        tags=data.get('tags', ''),
        published=data.get('published', False)
    )
    
    db.session.add(article)
    db.session.commit()
    return jsonify(article.to_json()), 201

# ============= COMMENT ROUTES =============

@app.route('/api/projects/<int:id>/comments', methods=['GET'])
def get_comments(id):
    comments = Comment.query.filter_by(project_id=id, approved=True).order_by(Comment.created_at.desc()).all()
    return jsonify([c.to_json() for c in comments])

@app.route('/api/projects/<int:id>/comments', methods=['POST'])
def add_comment(id):
    data = request.json
    comment = Comment(
        project_id=id,
        name=data['name'],
        email=data['email'],
        message=data['message'],
        rating=data.get('rating', 5)
    )
    db.session.add(comment)
    db.session.commit()
    return jsonify({"message": "Comment submitted for approval"}), 201

@app.route('/api/comments/<int:id>/approve', methods=['PUT'])
def approve_comment(id):
    comment = Comment.query.get_or_404(id)
    comment.approved = True
    db.session.commit()
    return jsonify({"message": "Comment approved"})

# ============= CONTACT ROUTES =============

@app.route('/api/contact', methods=['POST'])
def submit_contact():
    data = request.json
    contact = Contact(
        name=data['name'],
        email=data['email'],
        subject=data.get('subject'),
        message=data['message']
    )
    db.session.add(contact)
    db.session.commit()
    return jsonify({"message": "Message sent successfully"}), 201

@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    contacts = Contact.query.order_by(Contact.created_at.desc()).all()
    return jsonify([c.to_json() for c in contacts])

@app.route('/api/contacts/<int:id>/read', methods=['PUT'])
def mark_contact_read(id):
    contact = Contact.query.get_or_404(id)
    contact.read = True
    db.session.commit()
    return jsonify({"message": "Marked as read"})

# ============= UPLOAD ROUTES =============

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            "message": "File uploaded",
            "url": f"/uploads/{filename}"
        }), 201
    
    return jsonify({"error": "Invalid file type"}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ============= STATS/ANALYTICS ROUTES =============

@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = {
        "total_projects": Project.query.count(),
        "total_views": db.session.query(db.func.sum(Project.views)).scalar() or 0,
        "total_likes": db.session.query(db.func.sum(Project.likes)).scalar() or 0,
        "total_articles": Article.query.filter_by(published=True).count(),
        "total_skills": Skill.query.count(),
        "total_comments": Comment.query.filter_by(approved=True).count(),
        "unread_messages": Contact.query.filter_by(read=False).count(),
        "status": "ok"
    }
    return jsonify(stats)

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    # Recent projects
    recent_projects = Project.query.order_by(Project.created_at.desc()).limit(5).all()
    
    # Recent comments (unapproved)
    recent_comments = Comment.query.filter_by(approved=False).order_by(Comment.created_at.desc()).limit(5).all()
    
    # Recent contacts
    recent_contacts = Contact.query.filter_by(read=False).order_by(Contact.created_at.desc()).limit(5).all()
    
    # Popular projects
    popular_projects = Project.query.order_by(Project.views.desc()).limit(5).all()
    
    return jsonify({
        "recent_projects": [p.to_json() for p in recent_projects],
        "recent_comments": [c.to_json() for c in recent_comments],
        "recent_contacts": [c.to_json() for c in recent_contacts],
        "popular_projects": [p.to_json() for p in popular_projects]
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
