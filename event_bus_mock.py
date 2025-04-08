import threading
import time
import json
from queue import Queue
import datetime

class EventBusMock:
    """Implementação simulada do Event Bus para uso quando o Redis não está disponível"""

    def __init__(self):
        self.handlers = {}
        self.running = False
        self.thread = None
        self.queue = Queue()
        self.processed_events = 0
        self.start_time = datetime.datetime.now()

    def publish(self, event):
        """Publica um evento no barramento simulado"""
        self.queue.put(event)
        print(f"Evento publicado (simulado): {event['event_type']}")

    def register_handler(self, event_type, handler):
        """Registra um handler para um tipo de evento"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)

    def start(self):
        """Inicia o consumo de eventos"""
        self.running = True

        def listener():
            while self.running:
                try:
                    if not self.queue.empty():
                        event = self.queue.get(block=False)
                        event_type = event.get('event_type')

                        if event_type in self.handlers:
                            for handler in self.handlers[event_type]:
                                try:
                                    handler(event)
                                    self.processed_events += 1
                                    print(f"Evento processado (simulado): {event_type}")
                                except Exception as e:
                                    print(f"Erro ao processar evento {event_type}: {e}")
                except Exception as e:
                    print(f"Erro no listener simulado: {e}")

                time.sleep(0.1)  # Pequena pausa para não sobrecarregar a CPU

        self.thread = threading.Thread(target=listener)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Para o consumo de eventos"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def get_stats(self):
        """Retorna estatísticas do Event Bus simulado"""
        uptime = datetime.datetime.now() - self.start_time
        return {
            'processed_events': self.processed_events,
            'registered_handlers': sum(len(handlers) for handlers in self.handlers.values()),
            'event_types': list(self.handlers.keys()),
            'uptime_seconds': uptime.total_seconds(),
            'queue_size': self.queue.qsize()
        }
