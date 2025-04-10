from tinydb import TinyDB, Query

class ReadModel:
    def __init__(self, db_path='readmodel.json'):
        self.db = TinyDB(db_path)
        self.users = self.db.table('users')
        self.items = self.db.table('items')
        self.roles = self.db.table('roles')

    def get_user(self, user_id):
        """Obtém um usuário pelo ID"""
        User = Query()
        return self.users.get(User.id == user_id)

    def get_user_by_username(self, username):
        """Obtém um usuário pelo nome de usuário"""
        User = Query()
        return self.users.get(User.username == username)

    def get_user_by_email(self, email):
        """Obtém um usuário pelo email"""
        User = Query()
        return self.users.get(User.email == email)

    def get_users(self):
        """Obtém todos os usuários"""
        return self.users.all()

    def get_roles(self):
        """Obtém todos os perfis"""
        return self.roles.all()

    def get_role(self, role_id):
        """Obtém um perfil pelo ID"""
        Role = Query()
        return self.roles.get(Role.id == role_id)

    def save_role(self, role_data):
        """Salva um perfil"""
        Role = Query()
        # Verificar se o perfil já existe
        existing_role = self.roles.get(Role.id == role_data.get('id'))

        if existing_role:
            # Atualizar perfil existente
            self.roles.update(role_data, Role.id == role_data.get('id'))
        else:
            # Inserir novo perfil
            self.roles.insert(role_data)

    def save_user(self, user_data):
        """Salva ou atualiza um usuário"""
        User = Query()
        if self.users.contains(User.id == user_data['id']):
            self.users.update(user_data, User.id == user_data['id'])
        else:
            self.users.insert(user_data)

    def delete_user(self, user_id):
        """Remove um usuário"""
        User = Query()
        self.users.remove(User.id == user_id)

    def get_item(self, item_id):
        """Obtém um item pelo ID"""
        Item = Query()
        return self.items.get(Item.id == item_id)

    def get_items(self, user_id=None):
        """Obtém todos os itens, opcionalmente filtrados por user_id"""
        if user_id:
            Item = Query()
            return self.items.search(Item.user_id == user_id)
        return self.items.all()

    def save_item(self, item_data):
        """Salva ou atualiza um item"""
        Item = Query()
        if self.items.contains(Item.id == item_data['id']):
            self.items.update(item_data, Item.id == item_data['id'])
        else:
            self.items.insert(item_data)

    def delete_item(self, item_id):
        """Remove um item"""
        Item = Query()
        self.items.remove(Item.id == item_id)

    def delete_user(self, user_id):
        """Remove um usuário"""
        User = Query()
        self.users.remove(User.id == user_id)
