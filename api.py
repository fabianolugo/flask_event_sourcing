from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource
from .models import User, Item, db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user, login_required

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

class UserRegistration(Resource):
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

class UserLogin(Resource):
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

class ItemResource(Resource):
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
api.add_resource(UserRegistration, '/register')
api.add_resource(UserLogin, '/login')
api.add_resource(ItemResource, '/items', '/items/<int:item_id>')
