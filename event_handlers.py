from read_model import ReadModel

class EventHandlers:
    def __init__(self):
        self.read_model = ReadModel()

    def handle_user_created(self, event):
        """Manipula eventos de criação de usuário"""
        # Verificar se os dados já estão deserializados
        if isinstance(event['data'], str):
            import json
            user_data = json.loads(event['data'])
        else:
            user_data = event['data']

        # Criar uma cópia para não modificar o original
        user_data = dict(user_data)
        user_data['id'] = event['aggregate_id']
        self.read_model.save_user(user_data)

    def handle_user_updated(self, event):
        """Manipula eventos de atualização de usuário"""
        # Verificar se os dados já estão deserializados
        if isinstance(event['data'], str):
            import json
            user_data = json.loads(event['data'])
        else:
            user_data = event['data']

        # Criar uma cópia para não modificar o original
        user_data = dict(user_data)
        user_data['id'] = event['aggregate_id']
        self.read_model.save_user(user_data)

    def handle_user_deleted(self, event):
        """Manipula eventos de exclusão de usuário"""
        user_id = event['aggregate_id']
        self.read_model.delete_user(user_id)

    def handle_item_created(self, event):
        """Manipula eventos de criação de item"""
        # Verificar se os dados já estão deserializados
        if isinstance(event['data'], str):
            import json
            item_data = json.loads(event['data'])
        else:
            item_data = event['data']

        # Criar uma cópia para não modificar o original
        item_data = dict(item_data)
        item_data['id'] = event['aggregate_id']
        self.read_model.save_item(item_data)

    def handle_item_updated(self, event):
        """Manipula eventos de atualização de item"""
        # Verificar se os dados já estão deserializados
        if isinstance(event['data'], str):
            import json
            item_data = json.loads(event['data'])
        else:
            item_data = event['data']

        # Criar uma cópia para não modificar o original
        item_data = dict(item_data)
        item_data['id'] = event['aggregate_id']
        self.read_model.save_item(item_data)

    def handle_item_deleted(self, event):
        """Manipula eventos de exclusão de item"""
        # Verificar se os dados já estão deserializados
        if isinstance(event['data'], str):
            import json
            deletion_info = json.loads(event['data'])
        else:
            deletion_info = event['data']

        # Obter o ID do item a ser excluído
        item_id = event['aggregate_id']

        # Registrar informações sobre a exclusão (opcional)
        print(f"Item {item_id} excluído em {deletion_info.get('deleted_at', 'data desconhecida')}")

        # Remover o item do Read Model
        self.read_model.delete_item(item_id)

    def handle_user_deleted(self, event):
        """Manipula eventos de exclusão de usuário"""
        # Obter o ID do usuário
        user_id = event['aggregate_id']

        # Verificar se os dados já estão deserializados
        if isinstance(event['data'], str):
            import json
            deletion_info = json.loads(event['data'])
        else:
            deletion_info = event['data']

        # Registrar informações sobre a exclusão (opcional)
        print(f"Usuário {user_id} excluído em {deletion_info.get('deleted_at', 'data desconhecida')}")

        # Remover o usuário do Read Model
        self.read_model.delete_user(user_id)

    def handle_test_event(self, event):
        """Manipula eventos de teste"""
        # Obter o ID do agregado
        aggregate_id = event['aggregate_id']

        # Verificar se os dados já estão deserializados
        if isinstance(event['data'], str):
            import json
            data = json.loads(event['data'])
        else:
            data = event['data']

        # Registrar informações sobre o evento de teste
        print(f"Evento de teste recebido: {aggregate_id}")
        print(f"Mensagem: {data.get('message', 'Sem mensagem')}")
        print(f"Timestamp: {data.get('timestamp', 'Sem timestamp')}")
