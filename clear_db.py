from basic_app import app, db, User, Item

# Usar o contexto da aplicação
with app.app_context():
    # Deletar todos os itens
    Item.query.delete()
    
    # Deletar todos os usuários
    User.query.delete()
    
    # Commit das alterações
    db.session.commit()
    
    print("Todos os usuários e itens foram removidos do banco de dados.")
