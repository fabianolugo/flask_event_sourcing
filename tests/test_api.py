import unittest
import json
from app import create_app
from models import db, User, Item

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create a test user
            user = User(username='testuser', email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
    
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_user_registration(self):
        response = self.client.post('/api/register', 
                                   data=json.dumps({
                                       'username': 'newuser',
                                       'email': 'new@example.com',
                                       'password': 'password123'
                                   }),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'User created successfully')
        
        with self.app.app_context():
            user = User.query.filter_by(username='newuser').first()
            self.assertIsNotNone(user)
    
    def test_user_login(self):
        response = self.client.post('/api/login', 
                                   data=json.dumps({
                                       'username': 'testuser',
                                       'password': 'password123'
                                   }),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Login successful')
        self.assertEqual(data['username'], 'testuser')
    
    def test_invalid_login(self):
        response = self.client.post('/api/login', 
                                   data=json.dumps({
                                       'username': 'testuser',
                                       'password': 'wrongpassword'
                                   }),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Invalid credentials')

if __name__ == '__main__':
    unittest.main()
