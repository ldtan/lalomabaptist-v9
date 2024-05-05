from typing import Dict

from flask import (
    abort,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_security import current_user

from ..auth.constants import Permission
from ..core.database import DbModel
from .models import SitePage


def _get_page_data(page: SitePage) -> Dict:
    if page.url_title == 'home':
        pass

def _get_models() -> Dict[str, DbModel]:
    from . import models

    sqla_models = (
        models.BulletinPost,
        models.Event,
        models.Ministry,
        models.Preaching,
    )

    return {model.__name__: model for model in sqla_models}

def display_page(title: str) -> str:
    page: SitePage = SitePage.query\
            .filter_by(url_title=title).first_or_404()
    
    if not page.active:
        abort(401)
    elif not page.access_node.has_user_permissions(
        current_user,
        Permission.READ_RECORD
    ):
        if current_user.is_authenticated:
            abort(403)
        else:
            return redirect(url_for('security.login', next=request.path))

    return render_template(
        f"pages/{page.template_name}",
        current_page=page,
        models=_get_models(),
    )
