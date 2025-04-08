from flask import Flask, render_template, flash, redirect, url_for, request, Blueprint, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_restful import Api, Resource
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-for-testing'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Define models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('Item', backref='owner', lazy='dynamic')

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

# Define forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different one.')

class ItemForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    submit = SubmitField('Submit')

# User loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    items = Item.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', title='Dashboard', items=items)

@app.route('/item/new', methods=['GET', 'POST'])
@login_required
def new_item():
    form = ItemForm()
    if form.validate_on_submit():
        item = Item(title=form.title.data, description=form.description.data, owner=current_user)
        db.session.add(item)
        db.session.commit()
        flash('Your item has been created!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('create_item.html', title='New Item', form=form)

@app.route('/item/<int:item_id>')
@login_required
def item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('You do not have permission to view this item.', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('item.html', title=item.title, item=item)

@app.route('/item/<int:item_id>/update', methods=['GET', 'POST'])
@login_required
def update_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('You do not have permission to update this item.', 'danger')
        return redirect(url_for('dashboard'))
    form = ItemForm()
    if form.validate_on_submit():
        item.title = form.title.data
        item.description = form.description.data
        db.session.commit()
        flash('Your item has been updated!', 'success')
        return redirect(url_for('item', item_id=item.id))
    elif request.method == 'GET':
        form.title.data = item.title
        form.description.data = item.description
    return render_template('create_item.html', title='Update Item', form=form)

@app.route('/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('You do not have permission to delete this item.', 'danger')
        return redirect(url_for('dashboard'))
    db.session.delete(item)
    db.session.commit()
    flash('Your item has been deleted!', 'success')
    return redirect(url_for('dashboard'))

# API routes
api_bp = Blueprint('api', __name__)
api = Api(api_bp)

class UserRegistrationAPI(Resource):
    def post(self):
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return {'message': 'Missing required fields'}, 400
        
        if User.query.filter_by(username=data['username']).first():
            return {'message': 'Username already exists'}, 400
            
        if User.query.filter_by(email=data['email']).first():
            return {'message': 'Email already exists'}, 400
        
        user = User(
            username=data['username'],
            email=data['email']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return {'message': 'User created successfully'}, 201

class UserLoginAPI(Resource):
    def post(self):
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return {'message': 'Missing required fields'}, 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if user and user.check_password(data['password']):
            return {
                'message': 'Login successful',
                'user_id': user.id,
                'username': user.username,
                'email': user.email
            }, 200
        
        return {'message': 'Invalid credentials'}, 401

class ItemResourceAPI(Resource):
    @login_required
    def get(self, item_id=None):
        if item_id:
            item = Item.query.get_or_404(item_id)
            if item.user_id != current_user.id:
                return {'message': 'Unauthorized'}, 403
            return {
                'id': item.id,
                'title': item.title,
                'description': item.description,
                'created_at': item.created_at.isoformat(),
                'user_id': item.user_id
            }
        else:
            items = Item.query.filter_by(user_id=current_user.id).all()
            return [{
                'id': item.id,
                'title': item.title,
                'description': item.description,
                'created_at': item.created_at.isoformat(),
                'user_id': item.user_id
            } for item in items]
    
    @login_required
    def post(self):
        data = request.get_json()
        
        if not data or not data.get('title'):
            return {'message': 'Title is required'}, 400
        
        item = Item(
            title=data['title'],
            description=data.get('description', ''),
            user_id=current_user.id
        )
        
        db.session.add(item)
        db.session.commit()
        
        return {
            'message': 'Item created successfully',
            'id': item.id,
            'title': item.title,
            'description': item.description,
            'created_at': item.created_at.isoformat(),
            'user_id': item.user_id
        }, 201
    
    @login_required
    def put(self, item_id):
        item = Item.query.get_or_404(item_id)
        
        if item.user_id != current_user.id:
            return {'message': 'Unauthorized'}, 403
        
        data = request.get_json()
        
        if not data or not data.get('title'):
            return {'message': 'Title is required'}, 400
        
        item.title = data['title']
        item.description = data.get('description', item.description)
        
        db.session.commit()
        
        return {
            'message': 'Item updated successfully',
            'id': item.id,
            'title': item.title,
            'description': item.description,
            'created_at': item.created_at.isoformat(),
            'user_id': item.user_id
        }
    
    @login_required
    def delete(self, item_id):
        item = Item.query.get_or_404(item_id)
        
        if item.user_id != current_user.id:
            return {'message': 'Unauthorized'}, 403
        
        db.session.delete(item)
        db.session.commit()
        
        return {'message': 'Item deleted successfully'}

# Register API resources
api.add_resource(UserRegistrationAPI, '/register')
api.add_resource(UserLoginAPI, '/login')
api.add_resource(ItemResourceAPI, '/items', '/items/<int:item_id>')

# Register blueprint
app.register_blueprint(api_bp, url_prefix='/api')

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
