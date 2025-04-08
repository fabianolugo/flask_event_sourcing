# Exemplo de configurações locais
# Copie este arquivo para config_local.py e adicione suas credenciais

def update_config(app):
    """Atualiza as configurações da aplicação com valores locais"""
    app.config.update(
        GOOGLE_OAUTH_CLIENT_ID='seu_client_id_aqui',
        GOOGLE_OAUTH_CLIENT_SECRET='seu_client_secret_aqui'
    )
