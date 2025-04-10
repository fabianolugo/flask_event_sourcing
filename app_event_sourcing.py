from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
import os
from dotenv import load_dotenv
import uuid
import json
from datetime import datetime, date
from forms import LoginForm, RegistrationForm, UpdateProfileForm, ChangePasswordForm, ItemForm
from flask_wtf.csrf import CSRFProtect

# Permitir OAuth sem HTTPS para desenvolvimento local
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Carregar variáveis de ambiente
load_dotenv()

# Importar componentes de Event Sourcing
from event_sourcing_config import setup_event_sourcing
from user_service import UserService
from item_service import ItemService
from admin_views import admin_bp
from auth_service import AuthService

# Configuração da aplicação
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'uma-chave-secreta-muito-segura-para-desenvolvimento')
app.config['PERMANENT_SESSION_LIFETIME'] = 60 * 60 * 24 * 7  # 1 semana
app.config['SESSION_COOKIE_SECURE'] = False  # Definir como True em produção
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['WTF_CSRF_ENABLED'] = False  # Desabilitar CSRF para simplificar

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
auth_service = AuthService(event_store, event_bus, read_model)

# Armazenar o Auth Service na configuração da aplicação
app.config['AUTH_SERVICE'] = auth_service

# Garantir que o usuário admin seja criado
print("Verificando se o usuário admin existe...")
auth_service._create_admin_user_if_not_exists()
print("Verificação do usuário admin concluída.")

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

# Rotas para gerenciamento de usuários
@app.route('/manage-users', methods=['GET'])
def manage_users():
    """Página de gerenciamento de usuários"""
    # Verificar se o usuário está logado
    if not is_logged_in():
        flash('Você precisa estar logado para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    # Verificar se o usuário é administrador
    if not is_admin_user():
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))

    try:
        # Obter todos os usuários
        users = auth_service.get_all_users()

        # Obter todos os perfis
        roles = auth_service.get_roles()

        # Criar formulários
        from forms import AdminUserCreateForm, AdminUserEditForm
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

@app.route('/manage-users/create', methods=['POST'])
def create_user():
    """Cria um novo usuário pelo admin"""
    # Verificar se o usuário está logado
    if not is_logged_in():
        flash('Você precisa estar logado para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    # Verificar se o usuário é administrador
    if not is_admin_user():
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))

    # Processar formulário
    from forms import AdminUserCreateForm
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

    return redirect(url_for('manage_users'))

@app.route('/manage-users/edit', methods=['POST'])
def edit_user():
    """Edita um usuário pelo admin"""
    print("edit_user: Iniciando edição de usuário")

    # Verificar se o usuário está logado
    if not is_logged_in():
        print("edit_user: Usuário não está logado")
        flash('Você precisa estar logado para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    # Verificar se o usuário é administrador
    if not is_admin_user():
        print("edit_user: Usuário não é administrador")
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))

    print("edit_user: Processando formulário")
    # Processar formulário
    from forms import AdminUserEditForm
    form = AdminUserEditForm()

    print(f"edit_user: Formulário válido? {form.validate_on_submit()}")
    if form.validate_on_submit():
        # Obter ID do usuário a ser editado
        user_id = request.form.get('user_id')
        print(f"edit_user: ID do usuário a ser editado: {user_id}")

        if not user_id:
            print("edit_user: ID de usuário não fornecido")
            flash('ID de usuário não fornecido.', 'danger')
            return redirect(url_for('manage_users'))

        # Converter a data de nascimento para string ISO
        birth_date = None
        if form.birth_date.data:
            birth_date = form.birth_date.data.isoformat()
            print(f"edit_user: Data de nascimento: {birth_date}")

        # Obter o perfil do formulário
        role = request.form.get('role')
        print(f"edit_user: Perfil selecionado: {role}")

        # Preparar dados para atualização
        user_data = {
            'username': form.username.data,
            'email': form.email.data,
            'name': form.name.data,
            'birth_date': birth_date,
            'role': role
        }

        # Verificar se o usuário quer alterar a senha
        if form.change_password.data and form.password.data:
            print("edit_user: Alterando senha do usuário")
            user_data['password'] = form.password.data

        print(f"edit_user: Dados para atualização: {user_data}")

        # Atualizar usuário
        try:
            print("edit_user: Chamando auth_service.update_user")
            updated_user, error = auth_service.update_user(
                user_id=user_id,
                user_data=user_data
            )

            print(f"edit_user: Resultado da atualização: {updated_user}, Erro: {error}")

            if updated_user:
                print(f"edit_user: Usuário {updated_user['name']} atualizado com sucesso")
                flash(f'Usuário {updated_user["name"]} atualizado com sucesso!', 'success')
            else:
                print(f"edit_user: Erro ao atualizar usuário: {error}")
                flash(f'Erro ao atualizar usuário: {error}', 'danger')
        except Exception as e:
            print(f"edit_user: Exceção ao atualizar usuário: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Erro ao atualizar usuário: {str(e)}', 'danger')
    else:
        print("edit_user: Formulário inválido")
        for field, errors in form.errors.items():
            for error in errors:
                print(f"edit_user: Erro no campo {field}: {error}")
                flash(f'Erro no campo {getattr(form, field).label.text}: {error}', 'danger')

    print("edit_user: Redirecionando para manage_users")
    return redirect(url_for('manage_users'))

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

# Função para verificar se o usuário é administrador
def is_admin_user():
    user = get_current_user()
    if not user:
        return False
    return user.get('role') == 'admin'

# Função para verificar permissões do usuário
def has_permission(permission):
    user = get_current_user()
    if not user:
        return False

    # Obter o serviço de autenticação
    auth_service = app.config.get('AUTH_SERVICE')

    # Verificar permissão
    return auth_service.has_permission(user, permission)

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
        # Apenas se o Google estiver autorizado
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
                    'google_id': user_id,
                    'auth_type': 'google',
                    'created_at': datetime.now().isoformat()
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
                        'google_id': user_id,
                        'auth_type': 'google',
                        'created_at': datetime.now().isoformat()
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
    # Se o usuário estiver logado, redirecionar para o dashboard
    if is_logged_in():
        return redirect(url_for('dashboard'))

    # Se não estiver logado, redirecionar para a página de login
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('dashboard'))

    # Armazenar a URL de retorno na sessão
    session['next'] = request.args.get('next', url_for('dashboard'))

    # Criar formulário de login
    form = LoginForm()

    # Renderizar a página de login com opções de login local e Google
    return render_template('event_sourcing_login.html', form=form)

@app.route('/login/google')
def login_google():
    if is_logged_in():
        return redirect(url_for('dashboard'))

    return redirect(url_for('google.login'))

@app.route('/login/local', methods=['POST'])
def login_local():
    if is_logged_in():
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        # Autenticar usuário
        user, error = auth_service.authenticate_user(form.username.data, form.password.data)

        if user:
            # Salvar ID do usuário na sessão
            session.permanent = True
            session['user_id'] = user.get('id')
            session['user_name'] = user.get('name')

            flash('Login realizado com sucesso!', 'success')
            next_page = session.get('next', url_for('dashboard'))
            return redirect(next_page)
        else:
            flash(f'Falha no login: {error}', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Erro no campo {getattr(form, field).label.text}: {error}', 'danger')

    return redirect(url_for('login'))

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
            'google_id': user_id,
            'auth_type': 'google',
            'created_at': datetime.now().isoformat()
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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if is_logged_in():
        return redirect(url_for('dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Converter a data de nascimento para string ISO
        birth_date = None
        if form.birth_date.data:
            birth_date = form.birth_date.data.isoformat()

        # Registrar usuário
        user, error = auth_service.register_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            name=form.name.data,
            birth_date=birth_date
        )

        if user:
            # Salvar ID do usuário na sessão
            session.permanent = True
            session['user_id'] = user.get('id')
            session['user_name'] = user.get('name')

            flash('Cadastro realizado com sucesso! Bem-vindo(a)!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(f'Falha no cadastro: {error}', 'danger')

    return render_template('event_sourcing_register.html', form=form)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not is_logged_in():
        flash('Por favor, faça login para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    user = get_current_user()
    if not user:
        flash('Erro ao obter informações do usuário.', 'danger')
        return redirect(url_for('logout'))

    # Obter itens do usuário
    items = item_service.get_items(user.get('id'))

    # Formulário para atualização de perfil
    form = UpdateProfileForm()

    # Formulário para alteração de senha (apenas para usuários locais)
    password_form = ChangePasswordForm()

    # Preencher formulário com dados atuais
    if request.method == 'GET':
        form.username.data = user.get('username')
        form.email.data = user.get('email')
        form.name.data = user.get('name')

        # Converter a data de nascimento de string para objeto date
        if user.get('birth_date'):
            try:
                form.birth_date.data = date.fromisoformat(user.get('birth_date'))
            except (ValueError, TypeError):
                form.birth_date.data = None

    # Processar formulário de atualização de perfil
    if form.validate_on_submit():
        # Converter a data de nascimento para string ISO
        birth_date = None
        if form.birth_date.data:
            birth_date = form.birth_date.data.isoformat()

        # Atualizar usuário
        updated_user, error = auth_service.update_user(
            user_id=user.get('id'),
            user_data={
                'username': form.username.data,
                'email': form.email.data,
                'name': form.name.data,
                'birth_date': birth_date
            }
        )

        if updated_user:
            flash('Perfil atualizado com sucesso!', 'success')
            return redirect(url_for('profile'))
        else:
            flash(f'Falha ao atualizar perfil: {error}', 'danger')

    return render_template('event_sourcing_profile.html', user=user, form=form, password_form=password_form, items=items)

@app.route('/change-password', methods=['POST'])
def change_password():
    if not is_logged_in():
        flash('Por favor, faça login para acessar esta página.', 'danger')
        return redirect(url_for('login'))

    user = get_current_user()
    if not user:
        flash('Erro ao obter informações do usuário.', 'danger')
        return redirect(url_for('logout'))

    # Verificar se é um usuário local
    if user.get('auth_type') != 'local':
        flash('Apenas usuários com autenticação local podem alterar a senha.', 'danger')
        return redirect(url_for('profile'))

    form = ChangePasswordForm()
    if form.validate_on_submit():
        # Alterar senha
        success, error = auth_service.change_password(
            user_id=user.get('id'),
            current_password=form.current_password.data,
            new_password=form.new_password.data
        )

        if success:
            flash('Senha alterada com sucesso!', 'success')
        else:
            flash(f'Falha ao alterar senha: {error}', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Erro no campo {getattr(form, field).label.text}: {error}', 'danger')

    return redirect(url_for('profile'))

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
            'created_at': datetime.now().isoformat()
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
