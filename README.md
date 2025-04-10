# Sistema de Gerenciamento de Usuários com Event Sourcing

Uma aplicação web desenvolvida em Flask que implementa um sistema de gerenciamento de usuários utilizando a arquitetura Event Sourcing. Esta aplicação pode ser testada localmente e posteriormente convertida para Flutter.

## Funcionalidades

- **Autenticação de Usuários**:
  - Login tradicional com username/password
  - Login com Google OAuth
  - Registro de novos usuários

- **Gerenciamento de Usuários (Admin)**:
  - Criação de novos usuários
  - Edição de usuários existentes
  - Alteração de senhas
  - Exclusão de usuários
  - Atribuição de perfis (admin, creator, user)

- **Arquitetura Event Sourcing**:
  - Separação entre modelos de escrita e leitura
  - Armazenamento de eventos
  - Processamento assíncrono de eventos via Redis
  - Painel administrativo para visualização de eventos

- **Gerenciamento de Itens**:
  - Dashboard para gerenciar itens
  - Operações CRUD para itens

- **API RESTful**:
  - Endpoints para todas as operações

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual:
   ```
   python -m venv venv
   ```
3. Ative o ambiente virtual:
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source venv/bin/activate
     ```
4. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
5. Configure as variáveis de ambiente:
   - Crie um arquivo `.env` na raiz do projeto
   - Adicione as seguintes variáveis:
     ```
     SECRET_KEY=sua-chave-secreta
     GOOGLE_CLIENT_ID=seu-client-id-do-google
     GOOGLE_CLIENT_SECRET=seu-client-secret-do-google
     ```
6. Inicie o Redis (necessário para o Event Sourcing):
   ```
   # Instale o Redis e inicie o servidor
   # No Windows, você pode usar o Redis no WSL ou Docker
   ```

## Executando a Aplicação

1. Ative o ambiente virtual (se ainda não estiver ativado)
2. Execute a aplicação:
   ```
   python app_event_sourcing.py
   ```
3. Abra seu navegador e acesse `http://127.0.0.1:5000/`
4. Faça login com o usuário administrador padrão:
   - Username: admin
   - Senha: admin

## Endpoints da API

A aplicação fornece os seguintes endpoints de API:

- `POST /api/register` - Registrar um novo usuário
- `POST /api/login` - Fazer login
- `GET /api/items` - Obter todos os itens do usuário autenticado
- `GET /api/items/<item_id>` - Obter um item específico
- `POST /api/items` - Criar um novo item
- `PUT /api/items/<item_id>` - Atualizar um item
- `DELETE /api/items/<item_id>` - Excluir um item

## Estrutura do Projeto

- `app_event_sourcing.py`: Ponto de entrada da aplicação
- `auth_service.py`: Serviço de autenticação e gerenciamento de usuários
- `event_store.py`: Implementação do armazenamento de eventos
- `event_bus.py`: Implementação do barramento de eventos
- `read_model.py`: Implementação do modelo de leitura
- `event_handlers.py`: Manipuladores de eventos
- `admin_views.py`: Rotas e views para o painel administrativo
- `templates/`: Templates HTML
- `static/`: Arquivos estáticos (CSS, JS, imagens)

## Testes

Execute os testes usando pytest:

```
pytest
```

## Arquitetura Event Sourcing

A aplicação utiliza a arquitetura Event Sourcing, que consiste em:

1. **Event Store**: Armazena todos os eventos que ocorrem no sistema
2. **Event Bus**: Distribui eventos para os manipuladores apropriados
3. **Read Model**: Mantém uma visão otimizada para leitura dos dados
4. **Event Handlers**: Processam eventos e atualizam o Read Model

## Conversão para Flutter

Esta aplicação foi projetada para ser facilmente convertida para Flutter. Os endpoints da API RESTful podem ser consumidos por uma aplicação Flutter usando requisições HTTP.

Passos para converter para Flutter:

1. Criar um novo projeto Flutter
2. Configurar as dependências necessárias para requisições HTTP e gerenciamento de estado
3. Criar modelos que correspondam às respostas da API
4. Implementar telas para autenticação, dashboard e gerenciamento de usuários e itens
5. Conectar o aplicativo Flutter aos endpoints da API

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## Licença

Este projeto está licenciado sob a licença MIT.
