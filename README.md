# Flask Web Application

A simple web application built with Flask that can be tested locally and later converted to Flutter.

## Features

- User authentication (register, login, logout)
- Dashboard to manage items
- CRUD operations for items
- RESTful API endpoints

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source venv/bin/activate
     ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

1. Activate the virtual environment (if not already activated)
2. Run the application:
   ```
   python app.py
   ```
3. Open your browser and navigate to `http://127.0.0.1:5000/`

## API Endpoints

The application provides the following API endpoints:

- `POST /api/register` - Register a new user
- `POST /api/login` - Login a user
- `GET /api/items` - Get all items for the authenticated user
- `GET /api/items/<item_id>` - Get a specific item
- `POST /api/items` - Create a new item
- `PUT /api/items/<item_id>` - Update an item
- `DELETE /api/items/<item_id>` - Delete an item

## Testing

Run the tests using pytest:

```
pytest
```

## Converting to Flutter

This application is designed to be easily converted to Flutter. The RESTful API endpoints can be consumed by a Flutter application using HTTP requests.

Steps to convert to Flutter:

1. Create a new Flutter project
2. Set up the necessary dependencies for HTTP requests and state management
3. Create models that match the API responses
4. Implement screens for authentication, dashboard, and item management
5. Connect the Flutter app to the API endpoints

## License

This project is licensed under the MIT License.
