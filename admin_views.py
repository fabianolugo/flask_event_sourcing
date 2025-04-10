from flask import Blueprint, render_template, jsonify, current_app, request, redirect, url_for, flash
from forms import AdminUserCreateForm, AdminUserEditForm
from datetime import datetime, date
import json
import sqlite3
from tinydb import TinyDB
import redis
# Importações do sistema
# import os
# import sys

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Função auxiliar para verificar se o usuário é administrador
def is_admin(user):
    if not user:
        return False
    return user.get('role') == 'admin'

@admin_bp.route('/')
def admin_home():
    """Página inicial da administração"""
    # Verificar se o usuário está logado e é administrador
    from app_event_sourcing import get_current_user, is_logged_in

    if not is_logged_in():
        flash('Você precisa estar logado para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    user = get_current_user()
    if not is_admin(user):
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))

    return render_template('admin/index.html')

@admin_bp.route('/event-store')
def view_event_store():
    # Verificar se o usuário está logado e é administrador
    from app_event_sourcing import get_current_user, is_logged_in

    if not is_logged_in():
        flash('Você precisa estar logado para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    user = get_current_user()
    if not is_admin(user):
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))
    """Visualiza os eventos no Event Store"""
    try:
        conn = sqlite3.connect('events.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT 100")
        events = []
        for row in cursor.fetchall():
            event = dict(row)
            event['data'] = json.loads(event['data'])
            events.append(event)
        conn.close()
    except Exception as e:
        events = []
        print(f"Erro ao acessar o Event Store: {e}")

    return render_template('admin/event_store.html', events=events)

@admin_bp.route('/read-model')
def view_read_model():
    # Verificar se o usuário está logado e é administrador
    from app_event_sourcing import get_current_user, is_logged_in

    if not is_logged_in():
        flash('Você precisa estar logado para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    user = get_current_user()
    if not is_admin(user):
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))
    """Visualiza os dados no Read Model"""
    try:
        db = TinyDB('readmodel.json')
        users = db.table('users').all()
        items = db.table('items').all()
    except Exception as e:
        users = []
        items = []
        print(f"Erro ao acessar o Read Model: {e}")

    return render_template('admin/read_model.html', users=users, items=items)

@admin_bp.route('/message-queue')
def view_message_queue():
    # Verificar se o usuário está logado e é administrador
    from app_event_sourcing import get_current_user, is_logged_in

    if not is_logged_in():
        flash('Você precisa estar logado para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    user = get_current_user()
    if not is_admin(user):
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))
    """Visualiza informações sobre a fila de mensagens"""
    # Obter o Event Bus da configuração da aplicação
    event_bus = current_app.config.get('EVENT_BUS')

    # Inicializar queue_info com valores padrão
    queue_info = {
        'status': 'Disconnected',
        'redis_version': 'N/A',
        'connected_clients': 0,
        'used_memory_human': 'N/A',
        'pubsub_channels': [],
        'pubsub_patterns': [],
        'pubsub_numsub': [],
        'simulated': False
    }

    # Verificar se o Event Bus é uma instância de EventBus (Redis real)
    if event_bus and hasattr(event_bus, 'redis'):
        try:
            # Obter estatísticas do Redis através do Event Bus
            stats = event_bus.get_stats()

            # Verificar se o Redis está conectado
            if stats.get('status') == 'Disconnected':
                queue_info = {
                    'status': 'Disconnected',
                    'error': stats.get('error', 'Não foi possível conectar ao Redis'),
                    'simulated': False
                }
            else:
                queue_info = {
                    'status': 'Connected',
                    'redis_version': stats.get('redis_version'),
                    'connected_clients': stats.get('connected_clients'),
                    'used_memory_human': stats.get('used_memory_human'),
                    'pubsub_channels': stats.get('pubsub_channels', []),
                    'pubsub_patterns': stats.get('pubsub_patterns', []),
                    'pubsub_numsub': stats.get('pubsub_numsub', []),
                    'simulated': False,
                    'stats': stats
                }
        except Exception as e:
            queue_info['error'] = str(e)
            print(f"Erro ao obter estatísticas do Redis: {e}")
    # Verificar se o Event Bus é uma instância de EventBusMock (Redis simulado)
    elif event_bus and hasattr(event_bus, 'get_stats'):
        # Estamos usando o Event Bus simulado
        stats = event_bus.get_stats()
        queue_info = {
            'status': 'Simulated',
            'redis_version': 'N/A',
            'connected_clients': 0,
            'used_memory_human': 'N/A',
            'pubsub_channels': [],
            'pubsub_patterns': [],
            'pubsub_numsub': [],
            'simulated': True,
            'stats': stats
        }

    # Publicar um evento de teste no Redis para verificar se está funcionando
    if event_bus and hasattr(event_bus, 'publish') and queue_info['status'] != 'Disconnected':
        try:
            # Criar um evento de teste
            test_event = {
                'aggregate_id': 'test',
                'event_type': 'TEST_EVENT',
                'data': {
                    'message': 'Este é um evento de teste',
                    'timestamp': datetime.now().isoformat()
                }
            }

            # Publicar o evento
            event_bus.publish(test_event)
            print("Evento de teste publicado com sucesso!")
        except Exception as e:
            print(f"Erro ao publicar evento de teste: {e}")

    # Se não conseguimos obter estatísticas do Event Bus, tentar conectar diretamente ao Redis
    if queue_info['status'] == 'Disconnected':
        try:
            r = redis.Redis(host='localhost', port=6379, db=0)
            info = r.info()

            # Obter estatísticas de canais e mensagens
            pubsub_channels = r.pubsub_channels()
            pubsub_numsub = r.pubsub_numsub()

            # Publicar um evento de teste diretamente
            try:
                r.publish('events', '{"type":"TEST_EVENT","data":{"message":"Teste direto"}}')
                print("Evento de teste publicado diretamente no Redis!")
            except Exception as e:
                print(f"Erro ao publicar evento de teste diretamente: {e}")

            queue_info = {
                'status': 'Connected (Direct)',
                'redis_version': info.get('redis_version'),
                'connected_clients': info.get('connected_clients'),
                'used_memory_human': info.get('used_memory_human'),
                'pubsub_channels': pubsub_channels,
                'pubsub_patterns': r.pubsub_patterns(),
                'pubsub_numsub': pubsub_numsub,
                'simulated': False
            }
        except Exception as e:
            queue_info['error'] = str(e)
            print(f"Erro ao conectar ao Redis: {e}")

    return render_template('admin/message_queue.html', queue_info=queue_info)

@admin_bp.route('/users', methods=['GET'])
def admin_users():
    """Página de gerenciamento de usuários"""
    # Verificar se o usuário está logado e é administrador
    from app_event_sourcing import get_current_user, is_logged_in

    if not is_logged_in():
        flash('Você precisa estar logado para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    user = get_current_user()
    if not is_admin(user):
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))
    try:
        # Obter o serviço de autenticação
        auth_service = current_app.config.get('AUTH_SERVICE')

        # Obter todos os usuários
        users = auth_service.get_all_users()

        # Obter todos os perfis
        roles = auth_service.get_roles()

        # Criar formulários
        create_form = AdminUserCreateForm()
        edit_form = AdminUserEditForm()

        return render_template('admin/users.html',
                            users=users,
                            roles=roles,
                            create_form=create_form,
                            edit_form=edit_form)
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Erro ao carregar a página: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

@admin_bp.route('/users/create', methods=['POST'])
def admin_create_user():
    """Cria um novo usuário pelo admin"""
    # Verificar se o usuário está logado e é administrador
    from app_event_sourcing import get_current_user, is_logged_in

    if not is_logged_in():
        flash('Você precisa estar logado para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    user = get_current_user()
    if not is_admin(user):
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))

    # Obter o serviço de autenticação
    auth_service = current_app.config.get('AUTH_SERVICE')

    # Processar formulário
    form = AdminUserCreateForm()
    if form.validate_on_submit():
        # Converter a data de nascimento para string ISO
        birth_date = None
        if form.birth_date.data:
            birth_date = form.birth_date.data.isoformat()

        # Criar usuário
        new_user, error = auth_service.create_user_by_admin(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            name=form.name.data,
            role=request.form.get('role'),  # Obter o perfil do formulário
            birth_date=birth_date
        )

        if new_user:
            flash(f'Usuário {new_user["name"]} criado com sucesso!', 'success')
        else:
            flash(f'Erro ao criar usuário: {error}', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Erro no campo {getattr(form, field).label.text}: {error}', 'danger')

    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/users/edit', methods=['POST'])
def admin_edit_user():
    """Edita um usuário pelo admin"""
    # Verificar se o usuário está logado e é administrador
    from app_event_sourcing import get_current_user, is_logged_in

    if not is_logged_in():
        flash('Você precisa estar logado para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    user = get_current_user()
    if not is_admin(user):
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))

    # Obter o serviço de autenticação
    auth_service = current_app.config.get('AUTH_SERVICE')

    # Processar formulário
    form = AdminUserEditForm()
    if form.validate_on_submit():
        # Obter ID do usuário a ser editado
        user_id = request.form.get('user_id')
        if not user_id:
            flash('ID de usuário não fornecido.', 'danger')
            return redirect(url_for('admin.admin_users'))

        # Converter a data de nascimento para string ISO
        birth_date = None
        if form.birth_date.data:
            birth_date = form.birth_date.data.isoformat()

        # Preparar dados para atualização
        user_data = {
            'username': form.username.data,
            'email': form.email.data,
            'name': form.name.data,
            'birth_date': birth_date,
            'role': request.form.get('role')  # Obter o perfil do formulário
        }

        # Verificar se o usuário quer alterar a senha
        if form.change_password.data and form.password.data:
            user_data['password'] = form.password.data

        # Atualizar usuário
        updated_user, error = auth_service.update_user(
            user_id=user_id,
            user_data=user_data
        )

        if updated_user:
            flash(f'Usuário {updated_user["name"]} atualizado com sucesso!', 'success')
        else:
            flash(f'Erro ao atualizar usuário: {error}', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Erro no campo {getattr(form, field).label.text}: {error}', 'danger')

    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/users/delete/<user_id>', methods=['POST'])
def admin_delete_user(user_id):
    """Exclui um usuário pelo ID"""
    # Verificar se o usuário está logado e é administrador
    from app_event_sourcing import get_current_user, is_logged_in

    if not is_logged_in():
        flash('Você precisa estar logado para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    user = get_current_user()
    if not is_admin(user):
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))

    # Obter o serviço de autenticação
    auth_service = current_app.config.get('AUTH_SERVICE')

    # Excluir usuário
    success, error = auth_service.delete_user(user_id)

    if success:
        flash('Usuário excluído com sucesso!', 'success')
    else:
        flash(f'Erro ao excluir usuário: {error}', 'danger')

    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/api/events')
def api_events():
    """API para obter eventos em formato JSON"""
    try:
        conn = sqlite3.connect('events.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT 100")
        events = []
        for row in cursor.fetchall():
            event = dict(row)
            event['data'] = json.loads(event['data'])
            events.append(event)
        conn.close()
    except Exception as e:
        events = []
        print(f"Erro ao acessar o Event Store: {e}")

    return jsonify(events)

@admin_bp.route('/api/read-model')
def api_read_model():
    """API para obter dados do Read Model em formato JSON"""
    try:
        db = TinyDB('readmodel.json')
        data = {
            'users': db.table('users').all(),
            'items': db.table('items').all()
        }
    except Exception as e:
        data = {'users': [], 'items': []}
        print(f"Erro ao acessar o Read Model: {e}")

    return jsonify(data)
