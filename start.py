from app import app, db
from app.models import User, Application, Message, load_user, Group, Membership, Permission, Picture

app.config['SERVER_NAME'] = '127.0.0.1:5000'


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Application': Application, 'Message': Message,
            'Group': Group, 'Membership': Membership, 'Permission': Permission, "Picture": Picture, "load_user": load_user}
