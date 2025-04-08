import uuid

class ItemService:
    def __init__(self, event_store, event_bus, read_model):
        self.event_store = event_store
        self.event_bus = event_bus
        self.read_model = read_model

    def create_item(self, item_data):
        """Cria um novo item"""
        item_id = str(uuid.uuid4())

        # Criar e salvar o evento
        event = self.event_store.save_event(
            aggregate_id=item_id,
            event_type='ITEM_CREATED',
            data=item_data
        )

        # Publicar o evento
        self.event_bus.publish(event)

        return item_id

    def update_item(self, item_id, item_data):
        """Atualiza um item existente"""
        # Criar e salvar o evento
        event = self.event_store.save_event(
            aggregate_id=item_id,
            event_type='ITEM_UPDATED',
            data=item_data
        )

        # Publicar o evento
        self.event_bus.publish(event)

    def delete_item(self, item_id):
        """Remove um item"""
        # Obter o item antes de excluí-lo para armazenar seus dados no evento
        item = self.read_model.get_item(item_id)

        # Se o item não existir, usar um objeto vazio
        item_data = item if item else {}

        # Adicionar informações sobre a exclusão
        from datetime import datetime
        deletion_info = {
            'deleted_item': item_data,
            'deleted_at': datetime.now().isoformat(),
            'deletion_type': 'user_requested'
        }

        # Criar e salvar o evento
        event = self.event_store.save_event(
            aggregate_id=item_id,
            event_type='ITEM_DELETED',
            data=deletion_info
        )

        # Publicar o evento
        self.event_bus.publish(event)

    def get_item(self, item_id):
        """Obtém um item pelo ID (do modelo de leitura)"""
        return self.read_model.get_item(item_id)

    def get_items(self, user_id=None):
        """Obtém todos os itens, opcionalmente filtrados por user_id (do modelo de leitura)"""
        return self.read_model.get_items(user_id)
