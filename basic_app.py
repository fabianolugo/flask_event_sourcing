from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-for-testing'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///basic_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Define models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __repr__(self):
        return f'<Item {self.title}>'

# Create database tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    return render_template('basic_index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if username or email already exists
        user_exists = User.query.filter_by(username=username).first()
        email_exists = User.query.filter_by(email=email).first()
        
        if user_exists:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        
        if email_exists:
            flash('Email already exists. Please use a different one.', 'danger')
            return redirect(url_for('register'))
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('basic_register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('You have been logged in!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    
    return render_template('basic_login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))
    
    items = Item.query.filter_by(user_id=session['user_id']).all()
    return render_template('basic_dashboard.html', items=items)

@app.route('/item/new', methods=['GET', 'POST'])
def new_item():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        
        item = Item(title=title, description=description, user_id=session['user_id'])
        db.session.add(item)
        db.session.commit()
        
        flash('Your item has been created!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('basic_create_item.html')

@app.route('/item/<int:item_id>')
def item(item_id):
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))
    
    item = Item.query.get_or_404(item_id)
    
    if item.user_id != session['user_id']:
        flash('You do not have permission to view this item.', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('basic_item.html', item=item)

@app.route('/item/<int:item_id>/update', methods=['GET', 'POST'])
def update_item(item_id):
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))
    
    item = Item.query.get_or_404(item_id)
    
    if item.user_id != session['user_id']:
        flash('You do not have permission to update this item.', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        item.title = request.form['title']
        item.description = request.form['description']
        db.session.commit()
        
        flash('Your item has been updated!', 'success')
        return redirect(url_for('item', item_id=item.id))
    
    return render_template('basic_update_item.html', item=item)

@app.route('/item/<int:item_id>/delete', methods=['POST'])
def delete_item(item_id):
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))
    
    item = Item.query.get_or_404(item_id)
    
    if item.user_id != session['user_id']:
        flash('You do not have permission to delete this item.', 'danger')
        return redirect(url_for('dashboard'))
    
    db.session.delete(item)
    db.session.commit()
    
    flash('Your item has been deleted!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
