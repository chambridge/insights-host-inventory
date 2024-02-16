from flask_migrate import Migrate

from app import create_app
from app import db
from app.environment import RuntimeEnvironment

app = create_app(RuntimeEnvironment.COMMAND)
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db)
