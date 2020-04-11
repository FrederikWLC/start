from app import app, db
from app.models import User, Application, Message


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Application': Application, 'Message': Message}
