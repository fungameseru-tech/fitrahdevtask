import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:MaingamesDika%40123@db.lnjkikevajqklkfsjegd.supabase.co:5432/postgres'

from app import app, db, User, Category
from werkzeug.security import generate_password_hash

with app.app_context():
    # Create all tables
    db.create_all()
    print("✅ Database tables created!")
    
    # Check if admin exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@taskmaster.com',
            password_hash=generate_password_hash('Maingames123'),
            is_admin=True
        )
        db.session.add(admin)
        print("✅ Admin user created!")
    
    # Check if categories exist
    if Category.query.count() == 0:
        categories = [
            Category(name='Web Development'),
            Category(name='Mobile App'),
            Category(name='Design'),
            Category(name='Data Science'),
            Category(name='DevOps'),
            Category(name='Other')
        ]
        db.session.add_all(categories)
        print("✅ Default categories created!")
    
    db.session.commit()
    print("🎉 Supabase database initialized successfully!")
