import redis
import json
import threading
import time

class EventBus:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis = redis.Redis(host=host, port=port, db=db)
        self.pubsub = self.redis.pubsub()
        self.handlers = {}
        self.running = False
        self.thread = None

    def publish(self, event):
        """Publica um evento no barramento"""
        self.redis.publish('events', json.dumps(event))

    def register_handler(self, event_type, handler):
        """Registra um handler para um tipo de evento"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)

    def _message_handler(self, message):
        """Processa mensagens recebidas do Redis"""
        if message['type'] == 'message':
            event = json.loads(message['data'])
            event_type = event.get('event_type')

            if event_type in self.handlers:
                for handler in self.handlers[event_type]:
                    try:
                        handler(event)
                    except Exception as e:
                        print(f"Erro ao processar evento {event_type}: {e}")

    def start(self):
        """Inicia o consumo de eventos"""
        self.pubsub.subscribe('events')
        self.running = True

        def listener():
            while self.running:
                message = self.pubsub.get_message()
                if message:
                    self._message_handler(message)
                time.sleep(0.001)  # Pequena pausa para não sobrecarregar a CPU

        self.thread = threading.Thread(target=listener)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Para o consumo de eventos"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        self.pubsub.unsubscribe()

    def get_stats(self):
        """Retorna estatísticas do Redis"""
        try:
            info = self.redis.info()
            pubsub_channels = self.redis.pubsub_channels()
            pubsub_numsub = self.redis.pubsub_numsub()

            return {
                'redis_version': info.get('redis_version'),
                'connected_clients': info.get('connected_clients'),
                'used_memory_human': info.get('used_memory_human'),
                'uptime_seconds': info.get('uptime_in_seconds'),
                'total_commands_processed': info.get('total_commands_processed'),
                'pubsub_channels': pubsub_channels,
                'pubsub_patterns': self.redis.pubsub_patterns(),
                'pubsub_numsub': pubsub_numsub,
                'registered_handlers': sum(len(handlers) for handlers in self.handlers.values()),
                'event_types': list(self.handlers.keys())
            }
        except Exception as e:
            print(f"Erro ao obter estatísticas do Redis: {e}")
            return {
                'error': str(e),
                'registered_handlers': sum(len(handlers) for handlers in self.handlers.values()),
                'event_types': list(self.handlers.keys())
            }
