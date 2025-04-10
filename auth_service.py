import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class AuthService:
    # Definir perfis de usuário
    ROLES = {
        'admin': {
            'name': 'Administrador',
            'description': 'Acesso total ao sistema, incluindo gerenciamento de usuários e configurações',
            'permissions': ['manage_users', 'manage_items', 'view_admin']
        },
        'creator': {
            'name': 'Criador',
            'description': 'Pode criar e gerenciar itens',
            'permissions': ['manage_items']
        },
        'user': {
            'name': 'Usuário',
            'description': 'Acesso básico ao sistema',
            'permissions': ['view_items']
        }
    }

    def __init__(self, event_store, event_bus, read_model):
        self.event_store = event_store
        self.event_bus = event_bus
        self.read_model = read_model

        # Criar perfis se não existirem
        self._create_roles_if_not_exist()

        # Criar usuário admin se não existir
        self._create_admin_user_if_not_exists()

    def _create_roles_if_not_exist(self):
        """Cria os perfis padrão se não existirem"""
        roles = self.read_model.get_roles()

        # Se não houver perfis, criar os padrões
        if not roles:
            for role_id, role_data in self.ROLES.items():
                role_data['id'] = role_id
                self.read_model.save_role(role_data)
            print("Perfis padrão criados com sucesso!")

    def _create_admin_user_if_not_exists(self):
        """Cria um usuário admin padrão se não existir"""
        # Verificar se o usuário admin já existe
        admin = self._find_user_by_username('admin')
        print(f"_create_admin_user_if_not_exists: admin encontrado: {admin}")

        if not admin:
            # Criar usuário admin
            admin_id = str(uuid.uuid4())
            admin_data = {
                'username': 'admin',
                'email': 'admin@example.com',
                'name': 'Administrador',
                'password_hash': generate_password_hash('admin'),
                'role': 'admin',
                'created_at': datetime.now().isoformat(),
                'birth_date': None,
                'auth_type': 'local'  # Tipo de autenticação: local ou google
            }

            # Criar evento de usuário
            event = self.event_store.save_event(
                aggregate_id=admin_id,
                event_type='USER_CREATED',
                data=admin_data
            )

            # Publicar evento
            self.event_bus.publish(event)

            # Garantir que o usuário seja criado imediatamente no Read Model
            admin_data['id'] = admin_id
            self.read_model.save_user(admin_data)

            print("Usuário admin criado com sucesso!")
            print(f"ID do usuário admin: {admin_id}")

    def register_user(self, username, email, password, name, birth_date=None):
        """Registra um novo usuário local"""
        # Verificar se o usuário já existe
        existing_user = self._find_user_by_username(username)
        if existing_user:
            return None, "Nome de usuário já está em uso"

        existing_email = self._find_user_by_email(email)
        if existing_email:
            return None, "Email já está em uso"

        # Criar novo usuário
        user_id = str(uuid.uuid4())
        user_data = {
            'username': username,
            'email': email,
            'name': name,
            'password_hash': generate_password_hash(password),
            'role': 'user',
            'created_at': datetime.now().isoformat(),
            'birth_date': birth_date,
            'auth_type': 'local'  # Tipo de autenticação: local
        }

        # Criar evento de usuário
        event = self.event_store.save_event(
            aggregate_id=user_id,
            event_type='USER_CREATED',
            data=user_data
        )

        # Publicar evento
        self.event_bus.publish(event)

        # Obter usuário atualizado
        user = self.read_model.get_user(user_id)

        return user, None

    def authenticate_user(self, username, password):
        """Autentica um usuário local"""
        user = self._find_user_by_username(username)

        if not user:
            return None, "Usuário não encontrado"

        # Verificar se é um usuário local
        if user.get('auth_type') != 'local':
            return None, "Este usuário não usa autenticação local"

        # Verificar senha
        if not check_password_hash(user.get('password_hash', ''), password):
            return None, "Senha incorreta"

        return user, None

    def update_user(self, user_id, user_data):
        """Atualiza os dados de um usuário"""
        # Verificar se o usuário existe
        user = self.read_model.get_user(user_id)
        if not user:
            return None, "Usuário não encontrado"

        # Verificar se o nome de usuário já está em uso
        if 'username' in user_data and user_data['username'] != user.get('username'):
            existing_user = self._find_user_by_username(user_data['username'])
            if existing_user and existing_user.get('id') != user_id:
                return None, "Nome de usuário já está em uso"

        # Verificar se o email já está em uso
        if 'email' in user_data and user_data['email'] != user.get('email'):
            existing_email = self._find_user_by_email(user_data['email'])
            if existing_email and existing_email.get('id') != user_id:
                return None, "Email já está em uso"

        # Manter campos que não devem ser alterados
        user_data['auth_type'] = user.get('auth_type')

        # Verificar se o perfil é válido
        if 'role' in user_data and user_data['role'] not in self.ROLES:
            return None, f"Perfil inválido. Perfis válidos: {', '.join(self.ROLES.keys())}"

        # Se não houver perfil, manter o atual
        if 'role' not in user_data:
            user_data['role'] = user.get('role', 'user')

        # Se houver uma nova senha, fazer o hash
        if 'password' in user_data:
            user_data['password_hash'] = generate_password_hash(user_data.pop('password'))

        # Criar evento de atualização
        event = self.event_store.save_event(
            aggregate_id=user_id,
            event_type='USER_UPDATED',
            data=user_data
        )

        # Publicar evento
        self.event_bus.publish(event)

        # Garantir que o usuário seja atualizado imediatamente
        user_data['id'] = user_id
        self.read_model.save_user(user_data)

        # Obter usuário atualizado
        updated_user = self.read_model.get_user(user_id)

        return updated_user, None

    def create_user_by_admin(self, username, email, password, name, role='user', birth_date=None):
        """Permite que um administrador crie um novo usuário"""
        # Verificar se o usuário já existe
        existing_user = self._find_user_by_username(username)
        if existing_user:
            return None, "Nome de usuário já está em uso"

        existing_email = self._find_user_by_email(email)
        if existing_email:
            return None, "Email já está em uso"

        # Verificar se o perfil é válido
        if role not in self.ROLES:
            return None, f"Perfil inválido. Perfis válidos: {', '.join(self.ROLES.keys())}"

        # Criar novo usuário
        user_id = str(uuid.uuid4())
        user_data = {
            'username': username,
            'email': email,
            'name': name,
            'password_hash': generate_password_hash(password),
            'role': role,
            'created_at': datetime.now().isoformat(),
            'birth_date': birth_date,
            'auth_type': 'local',
            'created_by_admin': True
        }

        # Criar evento de usuário
        event = self.event_store.save_event(
            aggregate_id=user_id,
            event_type='USER_CREATED',
            data=user_data
        )

        # Publicar evento
        self.event_bus.publish(event)

        # Obter usuário atualizado
        user = self.read_model.get_user(user_id)

        return user, None

    def get_all_users(self):
        """Retorna todos os usuários"""
        return self.read_model.get_users()

    def get_user(self, user_id):
        """Retorna um usuário pelo ID"""
        return self.read_model.get_user(user_id)

    def get_roles(self):
        """Retorna todos os perfis disponíveis"""
        return self.ROLES

    def has_permission(self, user, permission):
        """Verifica se um usuário tem uma determinada permissão"""
        print(f"has_permission: Verificando permissão '{permission}' para usuário: {user}")

        if not user:
            print("has_permission: Usuário não encontrado")
            return False

        # Obter o perfil do usuário
        role = user.get('role', 'user')
        print(f"has_permission: Perfil do usuário: {role}")

        # Verificar se o perfil existe
        if role not in self.ROLES:
            print(f"has_permission: Perfil '{role}' não existe")
            return False

        # Verificar se a permissão está no perfil
        has_perm = permission in self.ROLES[role]['permissions']
        print(f"has_permission: Permissão '{permission}' encontrada no perfil '{role}'? {has_perm}")
        print(f"has_permission: Permissões disponíveis: {self.ROLES[role]['permissions']}")
        return has_perm

    def change_password(self, user_id, current_password, new_password):
        """Altera a senha de um usuário"""
        # Verificar se o usuário existe
        user = self.read_model.get_user(user_id)
        if not user:
            return False, "Usuário não encontrado"

        # Verificar se é um usuário local
        if user.get('auth_type') != 'local':
            return False, "Este usuário não usa autenticação local"

        # Verificar senha atual
        if not check_password_hash(user.get('password_hash', ''), current_password):
            return False, "Senha atual incorreta"

        # Atualizar senha
        user_data = {
            'password_hash': generate_password_hash(new_password)
        }

        # Criar evento de atualização
        event = self.event_store.save_event(
            aggregate_id=user_id,
            event_type='USER_PASSWORD_CHANGED',
            data=user_data
        )

        # Publicar evento
        self.event_bus.publish(event)

        # Garantir que o usuário seja atualizado imediatamente
        user_data['id'] = user_id
        self.read_model.save_user(user_data)

        return True, None

    def delete_user(self, user_id):
        """Exclui um usuário pelo ID"""
        # Verificar se o usuário existe
        user = self.read_model.get_user(user_id)
        if not user:
            return False, "Usuário não encontrado"

        # Não permitir excluir o usuário admin
        if user.get('username') == 'admin':
            return False, "Não é possível excluir o usuário administrador principal"

        # Criar evento de exclusão
        event = self.event_store.save_event(
            aggregate_id=user_id,
            event_type='USER_DELETED',
            data={'deleted_at': datetime.now().isoformat()}
        )

        # Publicar evento
        self.event_bus.publish(event)

        # Remover o usuário do Read Model imediatamente
        self.read_model.delete_user(user_id)

        return True, None

    def _find_user_by_username(self, username):
        """Encontra um usuário pelo nome de usuário"""
        users = self.read_model.get_users()
        print(f"_find_user_by_username: Procurando usuário com username '{username}' entre {len(users)} usuários")
        for user in users:
            if user.get('username') == username:
                print(f"_find_user_by_username: Usuário encontrado: {user}")
                return user
        print(f"_find_user_by_username: Usuário não encontrado")
        return None

    def _find_user_by_email(self, email):
        """Encontra um usuário pelo email"""
        users = self.read_model.get_users()
        for user in users:
            if user.get('email') == email:
                return user
        return None

    def update_user(self, user_id, user_data):
        """Atualiza um usuário existente"""
        print(f"update_user: Atualizando usuário {user_id} com dados: {user_data}")

        # Verificar se o usuário existe
        user = self.read_model.get_user(user_id)
        if not user:
            print(f"update_user: Usuário {user_id} não encontrado")
            return None, "Usuário não encontrado"

        print(f"update_user: Usuário encontrado: {user}")

        # Verificar se o nome de usuário já está em uso por outro usuário
        if 'username' in user_data and user_data['username'] != user.get('username'):
            existing_user = self._find_user_by_username(user_data['username'])
            if existing_user and existing_user.get('id') != user_id:
                print(f"update_user: Nome de usuário {user_data['username']} já está em uso")
                return None, "Nome de usuário já está em uso"

        # Verificar se o email já está em uso por outro usuário
        if 'email' in user_data and user_data['email'] != user.get('email'):
            existing_user = self._find_user_by_email(user_data['email'])
            if existing_user and existing_user.get('id') != user_id:
                print(f"update_user: Email {user_data['email']} já está em uso")
                return None, "Email já está em uso"

        # Verificar se o perfil é válido
        if 'role' in user_data and user_data['role'] not in self.ROLES:
            print(f"update_user: Perfil {user_data['role']} inválido")
            return None, f"Perfil inválido. Perfis válidos: {', '.join(self.ROLES.keys())}"

        # Manter dados que não devem ser alterados
        user_data['auth_type'] = user.get('auth_type')
        user_data['created_at'] = user.get('created_at')
        if 'password_hash' not in user_data:
            user_data['password_hash'] = user.get('password_hash')

        # Criar evento de atualização
        print(f"update_user: Criando evento de atualização para o usuário {user_id}")
        event = self.event_store.save_event(
            aggregate_id=user_id,
            event_type='USER_UPDATED',
            data=user_data
        )

        # Publicar evento
        print(f"update_user: Publicando evento de atualização")
        self.event_bus.publish(event)

        # Garantir que o usuário seja atualizado imediatamente no Read Model
        user_data['id'] = user_id
        print(f"update_user: Salvando usuário no Read Model: {user_data}")
        self.read_model.save_user(user_data)

        # Obter usuário atualizado
        updated_user = self.read_model.get_user(user_id)
        print(f"update_user: Usuário atualizado: {updated_user}")

        return updated_user, None
