# Event Sourcing Flask Application

Esta aplicação demonstra o padrão de arquitetura Event Sourcing usando Flask, com bancos de dados separados para escrita e leitura, conectados por um sistema de mensageria.

## Arquitetura

A aplicação utiliza:

1. **Event Store (Banco de Escrita)**: SQLite para armazenar eventos
2. **Read Model (Banco de Leitura)**: TinyDB (NoSQL) para consultas otimizadas
3. **Message Queue (Sistema de Mensageria)**: Redis para distribuição de eventos

## Requisitos

- Python 3.6+
- Redis (opcional, a aplicação funcionará em modo simulado se o Redis não estiver disponível)

## Instalação

1. Instale as dependências:
   ```
   cd flask_app
   .\venv\Scripts\pip install -r requirements.txt
   .\venv\Scripts\pip install tinydb redis
   ```

2. Configure as credenciais do Google OAuth:
   - Crie um projeto no [Google Cloud Console](https://console.cloud.google.com/)
   - Configure as credenciais OAuth 2.0
   - Adicione http://127.0.0.1:5000/login/google/authorized como URI de redirecionamento
   - Copie o Client ID e Client Secret para o arquivo `.env`

## Execução

Para executar a aplicação:

```
cd flask_app
.\venv\Scripts\python app_event_sourcing.py
```

Acesse a aplicação em http://127.0.0.1:5000/

## Funcionalidades

- **Autenticação com Google**: Login seguro usando OAuth 2.0
- **Gerenciamento de Itens**: Criar, visualizar, atualizar e excluir itens
- **Painel de Administração**: Visualizar eventos, modelo de leitura e fila de mensagens
- **API RESTful**: Endpoints para integração com aplicativos móveis

## Painel de Administração

O painel de administração permite visualizar os componentes internos da arquitetura Event Sourcing:

- **Event Store**: Visualize todos os eventos armazenados
- **Read Model**: Visualize o estado atual do sistema
- **Message Queue**: Visualize informações sobre a fila de mensagens

Acesse o painel de administração em http://127.0.0.1:5000/admin

## Estrutura do Projeto

- `app_event_sourcing.py`: Aplicação principal
- `event_store.py`: Implementação do Event Store
- `read_model.py`: Implementação do Read Model
- `event_bus.py`: Implementação do Event Bus
- `event_handlers.py`: Handlers para processar eventos
- `user_service.py`: Serviço para gerenciar usuários
- `item_service.py`: Serviço para gerenciar itens
- `admin_views.py`: Rotas para o painel de administração
- `templates/`: Templates HTML
- `static/`: Arquivos estáticos

## Modo Simulado

Se o Redis não estiver disponível, a aplicação usará um Event Bus simulado em memória. Isso permite que você execute a aplicação sem instalar o Redis, mas não oferece os benefícios de uma fila de mensagens distribuída.

## Conversão para Flutter

Esta aplicação foi projetada para ser facilmente convertida para Flutter. A API RESTful pode ser consumida por um aplicativo Flutter usando requisições HTTP.
