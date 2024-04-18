from flask_admin import Admin
from flask_babel import Babel
from flask_migrate import Migrate
from flask_security import Security
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

from .core.admin import AdminIndexView
from .core.database import DbModel


admin = Admin(index_view=AdminIndexView(), template_mode='bootstrap4')
babel = Babel()
db = SQLAlchemy(model_class=DbModel)
migrate = Migrate()
security = Security()
session = Session()
