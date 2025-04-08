import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Permitir OAuth sem HTTPS para desenvolvimento local
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from flask import Flask, redirect, url_for, render_template, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_dance.consumer import oauth_authorized
from sqlalchemy.orm.exc import NoResultFound

# Importar configurações
from config import Config

# Configuração da aplicação
app = Flask(__name__)
app.config.from_object(Config)

# Inicializar configurações
Config.init_app(app)

# Inicializar o banco de dados
db = SQLAlchemy(app)

# Definir modelos
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), unique=True)
    name = db.Column(db.String(256))
    avatar = db.Column(db.String(256))
    google_id = db.Column(db.String(256), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('Item', backref='owner', lazy='dynamic')

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# Configuração do blueprint do Google
google_bp = make_google_blueprint(
    client_id=app.config.get('GOOGLE_OAUTH_CLIENT_ID'),
    client_secret=app.config.get('GOOGLE_OAUTH_CLIENT_SECRET'),
    scope=[
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/userinfo.email',
        'openid'
    ],
    redirect_to='index'
)
app.register_blueprint(google_bp, url_prefix='/login')

# Criar tabelas do banco de dados
with app.app_context():
    db.create_all()

# Função para verificar se o usuário está logado
def is_logged_in():
    try:
        return google.authorized
    except Exception as e:
        print(f"Erro ao verificar autorização: {e}")
        return False

# Rotas
@app.route('/')
def index():
    return render_template('google_index.html', is_logged_in=is_logged_in())

@app.route('/login')
def login():
    if is_logged_in():
        return redirect(url_for('dashboard'))
    return redirect(url_for('google.login'))

@app.route('/logout')
def logout():
    try:
        if is_logged_in():
            # Remover token do Google
            token = google_bp.token
            if token:
                del google_bp.token
        # Limpar sessão em qualquer caso
        session.clear()
        flash('Você foi desconectado.', 'success')
    except Exception as e:
        print(f"Erro ao fazer logout: {e}")
        # Tentar limpar a sessão mesmo em caso de erro
        try:
            session.clear()
        except:
            pass
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if not is_logged_in():
        flash('Por favor, faça login para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    # Obter informações do usuário
    try:
        resp = google.get('/oauth2/v2/userinfo')
        if not resp.ok:
            flash('Falha ao obter informações do usuário.', 'danger')
            return redirect(url_for('logout'))

        google_info = resp.json()
        print(f"Google info: {google_info}")
        user = User.query.filter_by(google_id=google_info['id']).first()
    except Exception as e:
        print(f"Erro ao obter informações do usuário: {e}")
        flash('Erro ao obter informações do usuário.', 'danger')
        return redirect(url_for('logout'))

    # Se o usuário não existir, criar um novo
    if not user:
        user = User(
            email=google_info['email'],
            name=google_info.get('name', ''),
            avatar=google_info.get('picture', ''),
            google_id=google_info['id']
        )
        db.session.add(user)
        db.session.commit()

    # Obter itens do usuário
    items = Item.query.filter_by(user_id=user.id).all()
    return render_template('google_dashboard.html', user=user, items=items)

@app.route('/item/new', methods=['GET', 'POST'])
def new_item():
    from flask import request

    if not is_logged_in():
        flash('Por favor, faça login para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    # Obter informações do usuário
    try:
        resp = google.get('/oauth2/v2/userinfo')
        if not resp.ok:
            flash('Falha ao obter informações do usuário.', 'danger')
            return redirect(url_for('logout'))

        google_info = resp.json()
    except Exception as e:
        print(f"Erro ao obter informações do usuário: {e}")
        flash('Erro ao obter informações do usuário.', 'danger')
        return redirect(url_for('logout'))
    user = User.query.filter_by(google_id=google_info['id']).first()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']

        item = Item(title=title, description=description, user_id=user.id)
        db.session.add(item)
        db.session.commit()

        flash('Seu item foi criado!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('google_create_item.html')

@app.route('/item/<int:item_id>')
def item(item_id):
    if not is_logged_in():
        flash('Por favor, faça login para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    # Obter informações do usuário
    try:
        resp = google.get('/oauth2/v2/userinfo')
        if not resp.ok:
            flash('Falha ao obter informações do usuário.', 'danger')
            return redirect(url_for('logout'))

        google_info = resp.json()
        user = User.query.filter_by(google_id=google_info['id']).first()
    except Exception as e:
        print(f"Erro ao obter informações do usuário: {e}")
        flash('Erro ao obter informações do usuário.', 'danger')
        return redirect(url_for('logout'))

    item = Item.query.get_or_404(item_id)

    if item.user_id != user.id:
        flash('Você não tem permissão para visualizar este item.', 'danger')
        return redirect(url_for('dashboard'))

    return render_template('google_item.html', item=item)

@app.route('/item/<int:item_id>/update', methods=['GET', 'POST'])
def update_item(item_id):
    from flask import request

    if not is_logged_in():
        flash('Por favor, faça login para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    # Obter informações do usuário
    try:
        resp = google.get('/oauth2/v2/userinfo')
        if not resp.ok:
            flash('Falha ao obter informações do usuário.', 'danger')
            return redirect(url_for('logout'))

        google_info = resp.json()
        user = User.query.filter_by(google_id=google_info['id']).first()
    except Exception as e:
        print(f"Erro ao obter informações do usuário: {e}")
        flash('Erro ao obter informações do usuário.', 'danger')
        return redirect(url_for('logout'))

    item = Item.query.get_or_404(item_id)

    if item.user_id != user.id:
        flash('Você não tem permissão para atualizar este item.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        item.title = request.form['title']
        item.description = request.form['description']
        db.session.commit()

        flash('Seu item foi atualizado!', 'success')
        return redirect(url_for('item', item_id=item.id))

    return render_template('google_update_item.html', item=item)

@app.route('/item/<int:item_id>/delete', methods=['POST'])
def delete_item(item_id):
    if not is_logged_in():
        flash('Por favor, faça login para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    # Obter informações do usuário
    try:
        resp = google.get('/oauth2/v2/userinfo')
        if not resp.ok:
            flash('Falha ao obter informações do usuário.', 'danger')
            return redirect(url_for('logout'))

        google_info = resp.json()
        user = User.query.filter_by(google_id=google_info['id']).first()
    except Exception as e:
        print(f"Erro ao obter informações do usuário: {e}")
        flash('Erro ao obter informações do usuário.', 'danger')
        return redirect(url_for('logout'))

    item = Item.query.get_or_404(item_id)

    if item.user_id != user.id:
        flash('Você não tem permissão para excluir este item.', 'danger')
        return redirect(url_for('dashboard'))

    db.session.delete(item)
    db.session.commit()

    flash('Seu item foi excluído!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
