import uuid

class UserService:
    def __init__(self, event_store, event_bus, read_model):
        self.event_store = event_store
        self.event_bus = event_bus
        self.read_model = read_model
        
    def create_user(self, user_data):
        """Cria um novo usuário"""
        user_id = str(uuid.uuid4())
        
        # Criar e salvar o evento
        event = self.event_store.save_event(
            aggregate_id=user_id,
            event_type='USER_CREATED',
            data=user_data
        )
        
        # Publicar o evento
        self.event_bus.publish(event)
        
        return user_id
        
    def update_user(self, user_id, user_data):
        """Atualiza um usuário existente"""
        # Criar e salvar o evento
        event = self.event_store.save_event(
            aggregate_id=user_id,
            event_type='USER_UPDATED',
            data=user_data
        )
        
        # Publicar o evento
        self.event_bus.publish(event)
        
    def delete_user(self, user_id):
        """Remove um usuário"""
        # Criar e salvar o evento
        event = self.event_store.save_event(
            aggregate_id=user_id,
            event_type='USER_DELETED',
            data={}
        )
        
        # Publicar o evento
        self.event_bus.publish(event)
        
    def get_user(self, user_id):
        """Obtém um usuário pelo ID (do modelo de leitura)"""
        return self.read_model.get_user(user_id)
        
    def get_users(self):
        """Obtém todos os usuários (do modelo de leitura)"""
        return self.read_model.get_users()
