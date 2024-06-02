from datetime import datetime
from typing import (
    Any,
    Callable,
    Iterable,
    Optional,
    Tuple,
    Union,
)

from flask import (
    flash,
    redirect,
    request,
    url_for,
)
from flask_admin import (
    AdminIndexView as BaseAdminIndexView,
    expose,
)
from flask_admin.babel import gettext
from flask_admin.form.fields import Select2Field
from flask_admin.helpers import get_redirect_target
from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from sqlalchemy.orm import(
    DeclarativeBase,
    Session,
)
from wtforms import TextAreaField
from wtforms.widgets import TextArea

from .database import DbModel
from .localization import to_user_timezone


def _datetime_format(view, value: datetime):
    return to_user_timezone(value).strftime('%B %d, %Y, %I:%M %p')


class CKTextAreaWidget(TextArea):

    def __call__(self, field, **kwargs):
        kwargs.setdefault('class_', 'ckeditor')
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)


class CKTextAreaField(TextAreaField):
    
    widget = CKTextAreaWidget()


class Select2MultipleField(Select2Field):
    """Extends select2 field to make it work with postgresql arrays and using choices.
    
    Source Code: https://stackoverflow.com/questions/43576419/multiple-choices-in-flask-admin-form-choices
    """

    def iter_choices(self):
        """Iterate over choices especially to check if one of the values is
        selected.
        """

        if self.allow_blank:
            yield (u'__None', self.blank_text, self.data is None)

        for value, label in self.choices:
            yield (value, label, self.coerce(value) in self.data)

    def process_data(self, value):
        """This is called when you create the form with existing data."""

        if value is None:
            self.data = []
        else:
            try:
                self.data = [self.coerce(value) for value in value]
            except (ValueError, TypeError):
                self.data = []

    def process_formdata(self, valuelist):
        """Process posted data."""

        if not valuelist:
            return

        if valuelist[0] == '__None':
            self.data = []
        else:
            try:
                self.data = [self.coerce(value) for value in valuelist]
            except ValueError:
                raise ValueError(self.gettext(u'Invalid Choice: could not coerce'))

    def pre_validate(self, form):
        """Validate sent keys to make sure user don't post data that is not a
        valid choice.
        """

        sent_data = set(self.data)
        valid_data = {k for k, _ in self.choices}
        invalid_keys = sent_data - valid_data

        if invalid_keys:
            raise ValueError(f"These values are invalid {','.join(invalid_keys)}")


class AdminIndexView(BaseAdminIndexView):
    """Customized index view for Admin.
    
    Changes include:
        * Views are accessible only when user is authenticated.
        * Redirects to login page if user is not authenticated.
    """

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('security.login', next=request.path))
        
    def is_accessible(self):
        return current_user != None and current_user.is_authenticated


class AdminModelView(ModelView):
    """Customized ModelView for Admin.
    
    Changes include:
        * Views are accessible only when user is authenticated.
        * Redirects to login page if user is not authenticated.
        * Implements RBAC on a granular level (item level). It achieves this
          by being closely integrated with PermissionNode and PermissionMixin.
        * Allow definition of SQLA model, session, name and category during
          class declaration instead of instance creation.
    """

    model: Optional[DeclarativeBase] = None
    session: Optional[Session] = None
    name: Optional[str] = None
    category: Optional[str] = None

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    column_hide_backrefs = False
    column_type_formatters = {
        datetime: _datetime_format,
    }
    extra_js = ['//cdn.ckeditor.com/4.6.0/standard/ckeditor.js']

    def __init__(self, model=None, session=None, name=None, category=None,
            endpoint=None, url=None, static_folder=None, menu_class_name=None,
            menu_icon_type=None, menu_icon_value=None):
        super().__init__(
            model or self.model,
            session or self.session,
            name or self.name,
            category or self.category,
            endpoint, url, static_folder, menu_class_name, menu_icon_type, menu_icon_value,
        )

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            if not (current_user and current_user.is_authenticated):
                return redirect(url_for('security.login', next=request.path))
            else:
                return super()._handle_view(name, **kwargs)
    
    def is_accessible(self):
        return current_user != None and current_user.is_authenticated
    
    def has_create_permission(self) -> bool:
        """Override this method to add create permission checks on a granular
        level. By default, it returns True.
        """
        
        return True
    
    def has_details_permission(self, item: Optional[DbModel] = None) -> bool:
        """Override this method to add read permission checks on a granular
        level. By default, it returns True.
        """

        return True
    
    def has_edit_permission(self, item: Optional[DbModel] = None) -> bool:
        """Override this method to add edit permission checks on a granular
        level. By default, it returns True.
        """

        return True
    
    def has_delete_permission(self, item: Optional[DbModel] = None) -> bool:
        """Override this method to add delete permission checks on a granular
        level. By default, it returns True.
        """

        return True
    
    def delete_model(self, model):
        return self.has_delete_permission(model) \
                and super().delete_model(model)
    
    def update_records(self,
            ids: Iterable,
            record_editor: Callable[[Any], Tuple[Any, bool]]
        ) -> Iterable:

        query = self.model.query.filter(self.model.id.in_(ids))
        updated_records = []

        for record in query.all():
            record, is_updated = record_editor(record)

            if is_updated:
                updated_records.append(record)

        return updated_records

    
    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        return_url = get_redirect_target() or self.get_url('.index_view')
        
        if self.has_create_permission():
            return super().create_view()
        else:
            flash(gettext('User has no permission to create a record.'), 'error')
            return redirect(return_url)
    
    @expose('/details/')
    def details_view(self):
        item_id = int(request.args.get('id', None))
        return_url = get_redirect_target() or self.get_url('.index_view')

        if self.has_details_permission(self.model.query.get(item_id)):
            return super().details_view()
        else:
            flash(gettext('User has no permission to view this record.'), 'error')
            return redirect(return_url)
    
    @expose('/edit/', methods=('GET', 'POST'))
    def edit_view(self):
        item_id = int(request.args.get('id', None))
        return_url = get_redirect_target() or self.get_url('.index_view')

        if self.has_edit_permission(self.model.query.get(item_id)):
            return super().edit_view()
        else:
            flash(gettext('User has no permission to edit this record.'), 'error')
            return redirect(return_url)
    
    @expose('/delete/', methods=('POST',))
    def delete_view(self):
        form = self.delete_form()
        return_url = get_redirect_target() or self.get_url('.index_view')

        if self.has_delete_permission(self.model.query.get(form.id.data)):
            return super().delete_view()
        else:
            flash(gettext('User has no permission to delete this record.'), 'error')
            return redirect(return_url)
