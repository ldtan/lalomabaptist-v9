from flask import Blueprint
from sqlalchemy import event


def create_blueprint() -> Blueprint:
    from . import admin, models, views

    blueprint = Blueprint('base', __name__, url_prefix='/',
            static_folder=None, template_folder=None)
    
    blueprint.admin_views = (
        admin.MinistriesAdmin,
        admin.PeopleAdmin,
        admin.PreachingsAdmin,
        admin.SitePagesAdmin,
    )
    
    # blueprint.add_url_rule('/', view_func=views.index)

    return blueprint

def prepare_blueprint():
    from flask import current_app as app

    from ..auth.models import AccessNode
    from ..extensions import (
        db,
        security,
    )
    from .models import (
        BulletinPost,
        Event,
        Ministry,
        Person,
        Preaching,
        SitePage,
    )

    try:
        models = (
            BulletinPost,
            Event,
            Ministry,
            Person,
            Preaching,
            SitePage,
        )
        
        if not all(db.engine.dialect.has_table(db.session.connection(),
                model.__table__.name, model.__table__.schema) for model in models):
            return None
        
        if (base_access := AccessNode.get_by_full_name('base')) is None:
            base_access = AccessNode.create_by_full_name('base')

        # Create permission_node for models.
        for model in models:
            if (model_pn_name := getattr(model, 'access_node_full_name', None)) \
                    and AccessNode.get_by_full_name(model_pn_name) is None:
                AccessNode.create_by_full_name(model_pn_name)

        db.session.commit()
    
    except Exception:
        db.session.rollback()
        raise
