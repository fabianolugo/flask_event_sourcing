from tinydb import TinyDB, Query

class ReadModel:
    def __init__(self, db_path='readmodel.json'):
        self.db = TinyDB(db_path)
        self.users = self.db.table('users')
        self.items = self.db.table('items')
        
    def get_user(self, user_id):
        """Obtém um usuário pelo ID"""
        User = Query()
        return self.users.get(User.id == user_id)
        
    def get_users(self):
        """Obtém todos os usuários"""
        return self.users.all()
        
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
