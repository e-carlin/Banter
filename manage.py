# manage.py


from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from banter_api.app import create_app
from banter_api.extensions import db
from banter_api.models.user import User

app = create_app()

migrate = Migrate(app, db)
manager = Manager(app)

# migrations
manager.add_command('db', MigrateCommand)


@manager.command
def create_db():
    """Creates the db tables."""
    db.create_all()


@manager.command
def drop_db():
    """Drops the db tables."""
    db.drop_all()


if __name__ == '__main__':
    manager.run()
