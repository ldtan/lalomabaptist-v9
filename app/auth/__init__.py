from flask import Blueprint
from sqlalchemy import event


def create_blueprint() -> Blueprint:
    from . import admin, middleware, models, views

    blueprint = Blueprint('auth', __name__, url_prefix='/auth',
            static_folder=None, template_folder=None)
    
    blueprint.admin_views = (
        admin.AccessNodesAdmin,
        admin.RolesAdmin,
        admin.UsersAdmin,
        admin.GroupsAdmin,
        admin.UserAccessesAdmin,
        admin.GroupAccessesAdmin,
    )
    
    blueprint.add_url_rule('/', view_func=views.index)
    blueprint.add_url_rule('/task/sleep/', view_func=views.start_task)
    blueprint.add_url_rule('/task/<id>/', view_func=views.get_task)

    return blueprint

def prepare_blueprint():
    from flask import current_app as app

    from ..extensions import (
        db,
        security,
    )
    from .constants import (
        Permission,
        ANONYMOUS,
        AUTHENTICATED,
        SUPER_USER,
        CREATOR,
        EDITOR,
        CONTRIBUTOR,
        READER,
    )
    from .models import (
        Group,
        GroupAccess,
        AccessNode,
        Role,
        User,
        UserAccess,
    )

    datastore = security._datastore

    try:
        models = (
            Group,
            GroupAccess,
            AccessNode,
            Role,
            User,
            UserAccess,
        )
        
        if not all(db.engine.dialect.has_table(db.session.connection(),
                model.__table__.name, model.__table__.schema) for model in models):
            return None
        
        if (auth_access := AccessNode.get_by_full_name('auth')) is None:
            auth_access = AccessNode.create_by_full_name('auth')

        # Create permission_node for models.
        for model in models:
            if (model_pn_name := getattr(model, 'access_node_full_name', None)) \
                    and AccessNode.get_by_full_name(model_pn_name) is None:
                AccessNode.create_by_full_name(model_pn_name)

        super_user = datastore.find_or_create_role(SUPER_USER)
        super_user.permissions = [Permission.FULL_CONTROL.name]

        creator = datastore.find_or_create_role(CREATOR, permissions=[])
        creator.permissions = [
            Permission.CREATE_RECORD.name,
            Permission.EDIT_RECORD.name,
            Permission.READ_RECORD.name,
            Permission.DELETE_RECORD.name,
        ]

        editor = datastore.find_or_create_role(EDITOR)
        editor.permissions = [
            Permission.EDIT_RECORD.name,
            Permission.READ_RECORD.name,
            Permission.DELETE_RECORD.name,
        ]
        
        contributor = datastore.find_or_create_role(CONTRIBUTOR)
        contributor.permissions = [
            Permission.EDIT_RECORD.name,
            Permission.READ_RECORD.name,
        ]
        
        reader = datastore.find_or_create_role(READER)
        reader.permissions = [Permission.READ_RECORD.name]

        if Group.get_by_name(ANONYMOUS) is None:
            anonymous_group = Group(name=ANONYMOUS)
            db.session.add(anonymous_group)

        if Group.get_by_name(AUTHENTICATED) is None:
            authenticated_group = Group(name=AUTHENTICATED)
            db.session.add(authenticated_group)
        
        username = app.config.get('SUSER_USERNAME', None)
        email = app.config.get('SUSER_EMAIL', None)
        password = app.config.get('SUSER_PASSWORD', None)

        if User.query.count() == 0 and username and email and password:
            first_user = User.create_instance(
                username=username,
                email=email,
                password=password,
                active=True,
            )
            super_user_perm = UserAccess(
                access=auth_access,
                role=super_user,
                user=first_user
            )

            db.session.add(first_user)
            db.session.add(super_user_perm)

        db.session.commit()
    
    except Exception:
        db.session.rollback()
        raise
