from flask import Blueprint, render_template, jsonify, current_app
import json
import sqlite3
from tinydb import TinyDB
import redis
# Importações do sistema
# import os
# import sys

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
def admin_home():
    """Página inicial da administração"""
    return render_template('admin/index.html')

@admin_bp.route('/event-store')
def view_event_store():
    """Visualiza os eventos no Event Store"""
    try:
        conn = sqlite3.connect('events.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT 100")
        events = []
        for row in cursor.fetchall():
            event = dict(row)
            event['data'] = json.loads(event['data'])
            events.append(event)
        conn.close()
    except Exception as e:
        events = []
        print(f"Erro ao acessar o Event Store: {e}")

    return render_template('admin/event_store.html', events=events)

@admin_bp.route('/read-model')
def view_read_model():
    """Visualiza os dados no Read Model"""
    try:
        db = TinyDB('readmodel.json')
        users = db.table('users').all()
        items = db.table('items').all()
    except Exception as e:
        users = []
        items = []
        print(f"Erro ao acessar o Read Model: {e}")

    return render_template('admin/read_model.html', users=users, items=items)

@admin_bp.route('/message-queue')
def view_message_queue():
    """Visualiza informações sobre a fila de mensagens"""
    # Obter o Event Bus da configuração da aplicação
    event_bus = current_app.config.get('EVENT_BUS')

    # Inicializar queue_info com valores padrão
    queue_info = {
        'status': 'Disconnected',
        'redis_version': 'N/A',
        'connected_clients': 0,
        'used_memory_human': 'N/A',
        'pubsub_channels': [],
        'pubsub_patterns': [],
        'pubsub_numsub': [],
        'simulated': False
    }

    # Verificar se o Event Bus é uma instância de EventBus (Redis real)
    if event_bus and hasattr(event_bus, 'redis'):
        try:
            # Obter estatísticas do Redis através do Event Bus
            stats = event_bus.get_stats()
            queue_info = {
                'status': 'Connected',
                'redis_version': stats.get('redis_version'),
                'connected_clients': stats.get('connected_clients'),
                'used_memory_human': stats.get('used_memory_human'),
                'pubsub_channels': stats.get('pubsub_channels', []),
                'pubsub_patterns': stats.get('pubsub_patterns', []),
                'pubsub_numsub': stats.get('pubsub_numsub', []),
                'simulated': False,
                'stats': stats
            }
        except Exception as e:
            queue_info['error'] = str(e)
            print(f"Erro ao obter estatísticas do Redis: {e}")
    # Verificar se o Event Bus é uma instância de EventBusMock (Redis simulado)
    elif event_bus and hasattr(event_bus, 'get_stats'):
        # Estamos usando o Event Bus simulado
        stats = event_bus.get_stats()
        queue_info = {
            'status': 'Simulated',
            'redis_version': 'N/A',
            'connected_clients': 0,
            'used_memory_human': 'N/A',
            'pubsub_channels': [],
            'pubsub_patterns': [],
            'pubsub_numsub': [],
            'simulated': True,
            'stats': stats
        }

    # Se não conseguimos obter estatísticas do Event Bus, tentar conectar diretamente ao Redis
    if queue_info['status'] == 'Disconnected':
        try:
            r = redis.Redis(host='localhost', port=6379, db=0)
            info = r.info()

            # Obter estatísticas de canais e mensagens
            pubsub_channels = r.pubsub_channels()
            pubsub_numsub = r.pubsub_numsub()

            queue_info = {
                'status': 'Connected (Direct)',
                'redis_version': info.get('redis_version'),
                'connected_clients': info.get('connected_clients'),
                'used_memory_human': info.get('used_memory_human'),
                'pubsub_channels': pubsub_channels,
                'pubsub_patterns': r.pubsub_patterns(),
                'pubsub_numsub': pubsub_numsub,
                'simulated': False
            }
        except Exception as e:
            queue_info['error'] = str(e)
            print(f"Erro ao conectar ao Redis: {e}")

    return render_template('admin/message_queue.html', queue_info=queue_info)

@admin_bp.route('/api/events')
def api_events():
    """API para obter eventos em formato JSON"""
    try:
        conn = sqlite3.connect('events.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT 100")
        events = []
        for row in cursor.fetchall():
            event = dict(row)
            event['data'] = json.loads(event['data'])
            events.append(event)
        conn.close()
    except Exception as e:
        events = []
        print(f"Erro ao acessar o Event Store: {e}")

    return jsonify(events)

@admin_bp.route('/api/read-model')
def api_read_model():
    """API para obter dados do Read Model em formato JSON"""
    try:
        db = TinyDB('readmodel.json')
        data = {
            'users': db.table('users').all(),
            'items': db.table('items').all()
        }
    except Exception as e:
        data = {'users': [], 'items': []}
        print(f"Erro ao acessar o Read Model: {e}")

    return jsonify(data)
