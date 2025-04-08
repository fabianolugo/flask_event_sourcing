import sqlite3
import json
import uuid
from datetime import datetime

class EventStore:
    def __init__(self, db_path='events.db'):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            aggregate_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            data TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            version INTEGER NOT NULL
        )
        ''')
        conn.commit()
        conn.close()
        
    def save_event(self, aggregate_id, event_type, data):
        """Salva um novo evento no Event Store"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obter a versão atual do agregado
        cursor.execute(
            "SELECT MAX(version) FROM events WHERE aggregate_id = ?", 
            (aggregate_id,)
        )
        result = cursor.fetchone()
        version = (result[0] or 0) + 1
        
        # Criar o evento
        event = {
            'id': str(uuid.uuid4()),
            'aggregate_id': aggregate_id,
            'event_type': event_type,
            'data': json.dumps(data),
            'timestamp': datetime.utcnow().isoformat(),
            'version': version
        }
        
        # Salvar o evento
        cursor.execute(
            "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)",
            (
                event['id'], 
                event['aggregate_id'], 
                event['event_type'], 
                event['data'], 
                event['timestamp'], 
                event['version']
            )
        )
        conn.commit()
        conn.close()
        
        # Retornar o evento para ser publicado
        return event
        
    def get_events(self, aggregate_id=None):
        """Obtém eventos do Event Store, opcionalmente filtrados por aggregate_id"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if aggregate_id:
            cursor.execute(
                "SELECT * FROM events WHERE aggregate_id = ? ORDER BY version",
                (aggregate_id,)
            )
        else:
            cursor.execute("SELECT * FROM events ORDER BY timestamp")
            
        events = []
        for row in cursor.fetchall():
            event = dict(row)
            event['data'] = json.loads(event['data'])
            events.append(event)
            
        conn.close()
        return events
