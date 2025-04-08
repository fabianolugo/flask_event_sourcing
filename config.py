import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-testing'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Credenciais do Google OAuth (valores padrão vazios)
    GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')
    GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', '')

    # Tentar importar configurações locais
    @classmethod
    def init_app(cls, app):
        # Verificar se as credenciais foram configuradas
        if not cls.GOOGLE_OAUTH_CLIENT_ID or not cls.GOOGLE_OAUTH_CLIENT_SECRET:
            print("AVISO: Credenciais do Google OAuth não configuradas. Configure as variáveis de ambiente GOOGLE_OAUTH_CLIENT_ID e GOOGLE_OAUTH_CLIENT_SECRET.")

        # Tentar carregar configurações locais
        try:
            from config_local import update_config
            update_config(app)
            print("Configurações locais carregadas com sucesso.")
        except ImportError:
            print("Arquivo config_local.py não encontrado. Usando variáveis de ambiente.")
