from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
import os
from dotenv import load_dotenv
import uuid
import json

# Permitir OAuth sem HTTPS para desenvolvimento local
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Carregar variáveis de ambiente
load_dotenv()

# Importar componentes de Event Sourcing
from event_sourcing_config import setup_event_sourcing
from user_service import UserService
from item_service import ItemService
from admin_views import admin_bp

# Configuração da aplicação
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'uma-chave-secreta-muito-segura-para-desenvolvimento')
app.config['PERMANENT_SESSION_LIFETIME'] = 60 * 60 * 24 * 7  # 1 semana
app.config['SESSION_COOKIE_SECURE'] = False  # Definir como True em produção
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Configuração do Google OAuth
app.config['GOOGLE_OAUTH_CLIENT_ID'] = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')
app.config['GOOGLE_OAUTH_CLIENT_SECRET'] = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', '')

# Configurar Event Sourcing
es_components = setup_event_sourcing()
event_store = es_components['event_store']
read_model = es_components['read_model']
event_bus = es_components['event_bus']

# Armazenar o Event Bus na configuração da aplicação para acesso pelo painel de administração
app.config['EVENT_BUS'] = event_bus

# Inicializar serviços
user_service = UserService(event_store, event_bus, read_model)
item_service = ItemService(event_store, event_bus, read_model)

# Configuração do blueprint do Google
google_bp = make_google_blueprint(
    client_id=app.config.get('GOOGLE_OAUTH_CLIENT_ID'),
    client_secret=app.config.get('GOOGLE_OAUTH_CLIENT_SECRET'),
    scope=[
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/userinfo.email',
        'openid'
    ],
    redirect_url=None,  # Usar a URL padrão do Flask-Dance
    redirect_to='dashboard'  # Para onde redirecionar após o login bem-sucedido
)
app.register_blueprint(google_bp, url_prefix='/login')

# Registrar blueprint de administração
app.register_blueprint(admin_bp)

# Função para verificar se o usuário está logado
def is_logged_in():
    try:
        # Verificar se o token está na sessão
        if 'user_id' in session:
            return True
        # Verificar se o Google OAuth está autorizado
        if google.authorized:
            return True
        return False
    except Exception as e:
        print(f"Erro ao verificar autorização: {e}")
        return False

# Função para obter informações do usuário atual
def get_current_user():
    if not is_logged_in():
        return None

    try:
        # Verificar se já temos as informações do usuário na sessão
        if 'user_id' in session:
            user_id = session['user_id']
            # Buscar usuário do Read Model
            user = read_model.get_user(user_id)
            if user:
                return user

            # Se o usuário não estiver no Read Model, remover da sessão
            session.pop('user_id', None)
            session.pop('user_name', None)

        # Se não tiver na sessão ou o usuário não existir no Read Model, buscar do Google
        if not google.authorized:
            return None

        try:
            resp = google.get('/oauth2/v2/userinfo')
            if not resp.ok:
                return None

            user_info = resp.json()
            if not user_info or 'id' not in user_info:
                return None

            user_id = user_info.get('id')
            if not user_id:
                return None

            # Verificar se o usuário já existe no Read Model
            user = read_model.get_user(user_id)

            # Se o usuário não existir, criar um novo
            if not user:
                user_data = {
                    'name': user_info.get('name', ''),
                    'email': user_info.get('email', ''),
                    'avatar': user_info.get('picture', ''),
                    'google_id': user_id
                }

                # Criar evento de usuário
                event = event_store.save_event(
                    aggregate_id=user_id,
                    event_type='USER_CREATED',
                    data=user_data
                )

                # Publicar evento
                event_bus.publish(event)

                # Obter usuário atualizado
                user = read_model.get_user(user_id)

                # Se ainda não existir, criar um usuário básico
                if not user:
                    user = {
                        'id': user_id,
                        'name': user_info.get('name', ''),
                        'email': user_info.get('email', ''),
                        'avatar': user_info.get('picture', ''),
                        'google_id': user_id
                    }

            # Salvar ID do usuário na sessão
            if user:
                session.permanent = True
                session['user_id'] = user_id
                session['user_name'] = user.get('name', '')

            return user
        except Exception as e:
            print(f"Erro ao obter informações do usuário do Google: {e}")
            return None
    except Exception as e:
        print(f"Erro ao obter informações do usuário: {e}")
        return None

# Rotas
@app.route('/')
def index():
    user = get_current_user() if is_logged_in() else None
    return render_template('event_sourcing_index.html', is_logged_in=is_logged_in(), user=user)

@app.route('/login')
def login():
    if is_logged_in():
        return redirect(url_for('dashboard'))

    # Armazenar a URL de retorno na sessão
    session['next'] = request.args.get('next', url_for('dashboard'))

    return redirect(url_for('google.login'))

# Adicionar um manipulador de eventos para quando o usuário for autenticado
@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    if not token:
        flash('Falha ao fazer login com o Google.', 'danger')
        return False

    # Obter informações do usuário diretamente da API do Google
    resp = blueprint.session.get('/oauth2/v2/userinfo')
    if not resp.ok:
        flash('Falha ao obter informações do usuário.', 'danger')
        return False

    user_info = resp.json()
    user_id = user_info.get('id')

    if not user_id:
        flash('Falha ao obter ID do usuário.', 'danger')
        return False

    # Verificar se o usuário já existe no Read Model
    user = read_model.get_user(user_id)

    # Se o usuário não existir, criar um novo
    if not user:
        user_data = {
            'name': user_info.get('name', ''),
            'email': user_info.get('email', ''),
            'avatar': user_info.get('picture', ''),
            'google_id': user_id
        }

        # Criar evento de usuário
        event = event_store.save_event(
            aggregate_id=user_id,
            event_type='USER_CREATED',
            data=user_data
        )

        # Publicar evento
        event_bus.publish(event)

    # Salvar ID do usuário na sessão
    session.permanent = True
    session['user_id'] = user_id
    session['user_name'] = user_info.get('name', '')

    flash('Login realizado com sucesso!', 'success')

    # Evitar que o Flask-Dance salve o token novamente
    return False

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

    user = get_current_user()
    if not user:
        flash('Erro ao obter informações do usuário.', 'danger')
        return redirect(url_for('logout'))

    # Obter itens do usuário
    items = read_model.get_items(user.get('id'))

    # Verificar se há itens
    if items:
        # Formatar a data de criação para exibição
        for item in items:
            if 'created_at' in item:
                try:
                    from datetime import datetime
                    # Tentar converter a string ISO para um objeto datetime
                    dt = datetime.fromisoformat(item['created_at'])
                    # Formatar a data para exibição
                    item['created_at'] = dt.strftime('%d/%m/%Y %H:%M')
                except Exception as e:
                    print(f"Erro ao formatar data: {e}")
                    # Manter o valor original se houver erro

    return render_template('event_sourcing_dashboard.html', user=user, items=items)

@app.route('/item/new', methods=['GET', 'POST'])
def new_item():
    if not is_logged_in():
        flash('Por favor, faça login para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    user = get_current_user()
    if not user:
        flash('Erro ao obter informações do usuário.', 'danger')
        return redirect(url_for('logout'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']

        from datetime import datetime

        item_data = {
            'title': title,
            'description': description,
            'user_id': user.get('id'),
            'created_at': datetime.utcnow().isoformat()
        }

        # Criar item usando o serviço
        item_id = item_service.create_item(item_data)

        # Garantir que o item seja exibido imediatamente
        # Adicionar o item diretamente ao Read Model
        item_data['id'] = item_id
        read_model.save_item(item_data)

        flash('Seu item foi criado!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('event_sourcing_create_item.html', user=user)

@app.route('/item/<item_id>')
def item(item_id):
    if not is_logged_in():
        flash('Por favor, faça login para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    user = get_current_user()
    if not user:
        flash('Erro ao obter informações do usuário.', 'danger')
        return redirect(url_for('logout'))

    item = read_model.get_item(item_id)

    if not item or item.get('user_id') != user.get('id'):
        flash('Você não tem permissão para visualizar este item.', 'danger')
        return redirect(url_for('dashboard'))

    # Formatar a data de criação para exibição
    if 'created_at' in item:
        try:
            from datetime import datetime
            # Tentar converter a string ISO para um objeto datetime
            dt = datetime.fromisoformat(item['created_at'])
            # Formatar a data para exibição
            item['created_at'] = dt.strftime('%d/%m/%Y %H:%M')
        except Exception as e:
            print(f"Erro ao formatar data: {e}")
            # Manter o valor original se houver erro

    return render_template('event_sourcing_item.html', user=user, item=item)

@app.route('/item/<item_id>/update', methods=['GET', 'POST'])
def update_item(item_id):
    if not is_logged_in():
        flash('Por favor, faça login para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    user = get_current_user()
    if not user:
        flash('Erro ao obter informações do usuário.', 'danger')
        return redirect(url_for('logout'))

    item = read_model.get_item(item_id)

    if not item or item.get('user_id') != user.get('id'):
        flash('Você não tem permissão para atualizar este item.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']

        # Manter a data de criação original
        created_at = item.get('created_at')

        item_data = {
            'title': title,
            'description': description,
            'user_id': user.get('id'),
            'created_at': created_at
        }

        # Atualizar item usando o serviço
        item_service.update_item(item_id, item_data)

        # Garantir que o item seja atualizado imediatamente
        # Atualizar o item diretamente no Read Model
        item_data['id'] = item_id
        read_model.save_item(item_data)

        flash('Seu item foi atualizado!', 'success')
        return redirect(url_for('item', item_id=item_id))

    return render_template('event_sourcing_update_item.html', user=user, item=item)

@app.route('/item/<item_id>/delete', methods=['POST'])
def delete_item(item_id):
    if not is_logged_in():
        flash('Por favor, faça login para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    user = get_current_user()
    if not user:
        flash('Erro ao obter informações do usuário.', 'danger')
        return redirect(url_for('logout'))

    item = read_model.get_item(item_id)

    if not item or item.get('user_id') != user.get('id'):
        flash('Você não tem permissão para excluir este item.', 'danger')
        return redirect(url_for('dashboard'))

    # Excluir item usando o serviço
    item_service.delete_item(item_id)

    # Garantir que o item seja excluído imediatamente
    # Remover o item diretamente do Read Model
    read_model.delete_item(item_id)

    flash('Seu item foi excluído!', 'success')
    return redirect(url_for('dashboard'))

# API RESTful
@app.route('/api/items', methods=['GET'])
def api_get_items():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    items = read_model.get_items(user.get('id'))
    return jsonify(items)

@app.route('/api/items/<item_id>', methods=['GET'])
def api_get_item(item_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    item = read_model.get_item(item_id)

    if not item:
        return jsonify({'error': 'Item not found'}), 404

    if item.get('user_id') != user.get('id'):
        return jsonify({'error': 'Forbidden'}), 403

    return jsonify(item)

@app.route('/api/items', methods=['POST'])
def api_create_item():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.json
    if not data or not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400

    item_data = {
        'title': data.get('title'),
        'description': data.get('description', ''),
        'user_id': user.get('id')
    }

    # Criar item usando o serviço
    item_id = item_service.create_item(item_data)

    return jsonify({'id': item_id, 'message': 'Item created successfully'}), 201

@app.route('/api/items/<item_id>', methods=['PUT'])
def api_update_item(item_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    item = read_model.get_item(item_id)

    if not item:
        return jsonify({'error': 'Item not found'}), 404

    if item.get('user_id') != user.get('id'):
        return jsonify({'error': 'Forbidden'}), 403

    data = request.json
    if not data or not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400

    item_data = {
        'title': data.get('title'),
        'description': data.get('description', item.get('description', '')),
        'user_id': user.get('id')
    }

    # Atualizar item usando o serviço
    item_service.update_item(item_id, item_data)

    return jsonify({'message': 'Item updated successfully'})

@app.route('/api/items/<item_id>', methods=['DELETE'])
def api_delete_item(item_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    item = read_model.get_item(item_id)

    if not item:
        return jsonify({'error': 'Item not found'}), 404

    if item.get('user_id') != user.get('id'):
        return jsonify({'error': 'Forbidden'}), 403

    # Excluir item usando o serviço
    item_service.delete_item(item_id)

    # Garantir que o item seja excluído imediatamente
    # Remover o item diretamente do Read Model
    read_model.delete_item(item_id)

    return jsonify({'message': 'Item deleted successfully'})

if __name__ == '__main__':
    app.run(debug=True)
