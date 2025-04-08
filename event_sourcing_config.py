from event_store import EventStore
from read_model import ReadModel
from event_bus import EventBus
from event_handlers import EventHandlers

def setup_event_sourcing():
    # Inicializar componentes
    event_store = EventStore('events.db')
    read_model = ReadModel('readmodel.json')

    # Configurar o Redis real
    # Usar o Redis local na porta padrão 6379
    redis_host = 'localhost'
    redis_port = 6379
    redis_db = 0

    try:
        # Tentar conectar ao Redis real
        event_bus = EventBus(host=redis_host, port=redis_port, db=redis_db)
        print(f"Conectado ao Redis com sucesso em {redis_host}:{redis_port} (DB: {redis_db}).")

        # Verificar a conexão com o Redis
        info = event_bus.redis.info()
        print(f"Versão do Redis: {info.get('redis_version')}")
        print(f"Clientes conectados: {info.get('connected_clients')}")
        print(f"Memória utilizada: {info.get('used_memory_human')}")
    except Exception as e:
        print(f"Erro ao conectar ao Redis: {e}")
        print("Usando modo simulado para o Event Bus.")
        from event_bus_mock import EventBusMock
        event_bus = EventBusMock()

    handlers = EventHandlers()

    # Registrar handlers
    event_bus.register_handler('USER_CREATED', handlers.handle_user_created)
    event_bus.register_handler('USER_UPDATED', handlers.handle_user_updated)
    event_bus.register_handler('USER_DELETED', handlers.handle_user_deleted)
    event_bus.register_handler('ITEM_CREATED', handlers.handle_item_created)
    event_bus.register_handler('ITEM_UPDATED', handlers.handle_item_updated)
    event_bus.register_handler('ITEM_DELETED', handlers.handle_item_deleted)

    # Iniciar o event bus
    event_bus.start()

    return {
        'event_store': event_store,
        'read_model': read_model,
        'event_bus': event_bus
    }
