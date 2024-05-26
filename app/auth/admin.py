from typing import Optional
import uuid

from flask import request
from flask_admin.base import expose
from flask_admin.model.form import InlineFormAdmin
from flask_security import (
    current_user,
    hash_password,
    verify_password,
)
from flask_security import current_user
from sqlalchemy.orm import Query
from wtforms import (
    BooleanField,
    PasswordField,
)
from wtforms.validators import (
    EqualTo,
    ValidationError,
)

from ..core.admin import (
    AdminModelView,
    Select2MultipleField,
)
from ..core.auth import is_current_user_super
from ..core.database import DbModel
from ..core.utils import exclude
from .constants import (
    Permission,
    CONTRIBUTOR,
)
from .models import (
    AccessNode,
    GranularAccessMixin,
    Group,
    GroupAccess,
    Role,
    User,
    UserAccess,
)


def _group_query() -> Query:
    return Group.query.filter(
        (Group.name != 'Anonymous')
        & (Group.name != 'Authenticated')
    )


class AdminAccessModelView(AdminModelView):
    """Model View with AccessNode and GranularAccessMixin integrated."""

    form_extra_fields = {
        'use_unique_access': BooleanField('Use Unique Access?'),
    }

    def get_query(self):
        if issubclass(self.model, GranularAccessMixin):
            return self.model.authorized_query()
        else:
            query = super().get_query()
            return query if is_current_user_super() else \
                query.filter((self.model.id == 0) & (self.model.id != 0))
        
    # def get_list(self, page, sort_column, sort_desc, search,
    #         filters, execute=True, page_size=None):
        
    #     _, query = super().get_list(page, sort_column,
    #             sort_desc, search, filters, False, page_size)
        
    #     count = query.count()
    #     query = query.all() if execute else query

    #     return count, query
    
    def on_form_prefill(self, form, id):
        if not (issubclass(self.model, GranularAccessMixin)
                and getattr(form, 'use_unique_access', False)):
            return None
        
        item = self.model.query.get(id)
        form.use_unique_access.data = item.has_unique_access

    def on_model_change(self, form, model, is_created):
        if issubclass(self.model, GranularAccessMixin) \
                and hasattr(form, 'use_unique_access') \
                and (model_pn := self.model.get_model_access_node()) \
                and (item_pn := model.access_node) \
                and model.use_unique_access != model.has_unique_access:
            
            if model.use_unique_access:
                model.access_node = AccessNode.create_by_full_name(
                    f"{model_pn.full_name}.{model.uuid}",
                    user_accesses=item_pn.user_accesses,
                    group_accesses=item_pn.group_accesses,
                )
            else:
                self.session.delete(item_pn)
                model.access_node = model_pn

    def has_create_permission(self) -> bool:
        if is_current_user_super():
            return True
        
        access: AccessNode = self.model.get_model_access_node() \
                if hasattr(self.model, 'get_model_access_node') else None

        return access != None and access.has_user_permissions(
                current_user, Permission.CREATE_RECORD)
    
    def has_details_permission(self, item: DbModel | None = None) -> bool:
        if is_current_user_super():
            return True
        
        if item is None:
            access: AccessNode = self.model.get_model_access_node() \
                    if hasattr(self.model, 'get_model_access_node') else None
        else:
            access: AccessNode = getattr(item, 'access_node', None)

        return access != None and access.has_user_permissions(current_user,
                Permission.READ_RECORD)
    
    def has_edit_permission(self, item: DbModel | None = None) -> bool:
        if is_current_user_super():
            return True
        
        if item is None:
            access: AccessNode = self.model.get_model_access_node() \
                    if hasattr(self.model, 'get_model_access_node') else None
        else:
            access: AccessNode = getattr(item, 'access_node', None)

        return access != None and access.has_user_permissions(current_user,
                Permission.EDIT_RECORD)
    
    def has_delete_permission(self, item: DbModel | None = None) -> bool:
        if is_current_user_super():
            return True
        
        if item is None:
            access: AccessNode = self.model.get_model_access_node() \
                    if hasattr(self.model, 'get_model_access_node') else None
        else:
            access: AccessNode = getattr(item, 'access_node', None)

        return access != None and access.has_user_permissions(current_user,
                Permission.DELETE_RECORD)
    
    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        if issubclass(self.model, GranularAccessMixin):
            model_access = self.model.get_model_access_node()

            if model_access is None or not model_access.has_user_permissions(
                    current_user, Permission.ASSIGN_ACCESS):
                return super().create_view()
            
            access_ids = []
            access = model_access

            while access:
                access_ids.append(access.id)
                access = access.parent
            
            form_args_update = {
                'access_node': {
                    'query_factory': lambda: AccessNode.query\
                            .filter(AccessNode.id.in_(access_ids))\
                            .order_by(AccessNode.id.desc()),
                }
            }

            if self.form_args is None:
                self.form_args = form_args_update
            else:
                self.form_args.update(form_args_update)

            self._refresh_forms_cache()

        return super().create_view()
    
    @expose('/edit/', methods=('GET', 'POST'))
    def edit_view(self):
        if issubclass(self.model, GranularAccessMixin):
            model_access = self.model.get_model_access_node()
            item_id = int(request.args.get('id', None))
            item = self.model.query.get(item_id)

            if model_access is None or not model_access.has_user_permissions(
                    current_user, Permission.ASSIGN_ACCESS) or item is None:
                return super().edit_view()
            
            access_ids = []
            access = item.access_node

            while access:
                access_ids.append(access.id)
                access = access.parent

            if not access_ids:
                access_ids = [model_access.id] if model_access else [-1]
            
            form_args_update = {
                'access_node': {
                    'query_factory': lambda: AccessNode.query\
                            .filter(AccessNode.id.in_(access_ids))\
                            .order_by(AccessNode.id.desc()),
                }
            }

            if self.form_args is None:
                self.form_args = form_args_update
            else:
                self.form_args.update(form_args_update)

            self._refresh_forms_cache()

        return super().edit_view()
    

class AccessNodesAdmin(AdminAccessModelView):

    model = AccessNode

    class UserAccessInlineModel(InlineFormAdmin):
        form_columns = ('id', 'user', 'role',)

    class GroupAccessInlineModel(InlineFormAdmin):
        form_columns = ('id', 'group','role',)

    inline_models = (
        GroupAccessInlineModel(GroupAccess),
        UserAccessInlineModel(UserAccess),
    )
    column_list = ('full_name', 'created_at', 'updated_at',)
    column_filters = ('name', 'created_at', 'updated_at',)
    column_searchable_list = ('name',)
    form_columns = (
        'uuid',
        'created_at',
        'updated_at',
        'parent',
        'name',
        'user_accesses',
        'group_accesses',
    )
    column_details_list = form_columns
    form_create_rules = ('parent', 'name', 'user_accesses', 'group_accesses',)
    form_edit_rules = form_create_rules

    def get_query(self):
        return self.session.query(self.model)
    
    def has_create_permission(self) -> bool:
        if is_current_user_super():
            return True
        
        model_access: AccessNode = self.model.get_model_access_node()

        return model_access.has_user_permissions(
                current_user, Permission.READ_RECORD)
    
    def has_details_permission(self, item: DbModel | None = None) -> bool:
        if is_current_user_super():
            return True

        model_access: AccessNode = self.model.get_model_access_node()
        access: AccessNode = item

        return access.has_user_permissions(current_user, Permission.READ_ACCESS) \
                or model_access.has_user_permissions(current_user, Permission.READ_RECORD)
    
    def has_edit_permission(self, item: DbModel | None = None) -> bool:
        if is_current_user_super():
            return True

        model_access: AccessNode = self.model.get_model_access_node()
        access: AccessNode = item

        return access.has_user_permissions(current_user, Permission.EDIT_ACCESS) \
                or model_access.has_user_permissions(current_user, Permission.EDIT_RECORD)
    
    def has_delete_permission(self, item: DbModel | None = None) -> bool:
        if is_current_user_super():
            return True

        model_access: AccessNode = self.model.get_model_access_node()
        access: AccessNode = item

        return access.has_user_permissions(current_user, Permission.DELETE_ACCESS) \
                or model_access.has_user_permissions(current_user, Permission.DELETE_RECORD)
    

class RolesAdmin(AdminAccessModelView):

    model = Role

    column_list = ('name', 'created_at', 'updated_at',)
    column_filters = column_list
    column_searchable_list = ('name', 'description',)
    form_args = {
        'permissions': dict(
            render_kw={'multiple': 'multiple'},
            choices=Permission.items(),
        ),
    }
    form_overrides = {
        'permissions': Select2MultipleField,
    }
    form_columns = (
        'uuid',
        'created_at',
        'updated_at',
        'access_node',
        'use_unique_access',
        'name',
        'description',
        'permissions',
    )
    column_details_list = form_columns
    form_create_rules = (
        'access_node',
        'use_unique_access',
        'name',
        'description',
        'permissions',
    )
    form_edit_rules = form_create_rules


class UsersAdmin(AdminAccessModelView):

    model = User

    column_list = ('username', 'email', 'created_at', 'updated_at',)
    column_filters = column_list
    column_searchable_list = ('username', 'email',)
    form_extra_fields = {
        'use_unique_access': BooleanField('Use Unique Access?'),
        'old_password': PasswordField('Old Password'),
        'new_password': PasswordField(
            'New Password',
            validators=[
                EqualTo('confirm_password'),
            ]
        ),
        'confirm_password': PasswordField('Confirm New Password'),
    }
    form_args = {
        'groups': {
            'query_factory': _group_query,
        }
    }
    form_columns = (
        'uuid',
        'created_at',
        'updated_at',
        'access_node',
        'use_unique_access',
        'username',
        'email',
        'active',
        'old_password',
        'new_password',
        'confirm_password',
        'confirmed_at',
        'last_login_at',
        'current_login_at',
        'last_login_ip',
        'current_login_ip',
        'login_count',
        'groups',
    )
    column_details_list = exclude(form_columns,
            ('old_password', 'new_password', 'confirm_password',))
    form_create_rules = (
        'access_node',
        'use_unique_access',
        'username',
        'email',
        'new_password',
        'confirm_password',
        'active',
        'groups',
    )
    form_edit_rules = (
        'access_node',
        'use_unique_access',
        'username',
        'email',
        'old_password',
        'new_password',
        'confirm_password',
        'active',
        'groups',
    )

    def on_model_change(self, form, model, is_created) -> None:
        if len(model.new_password) > 0:
            if not is_created and \
                    not verify_password(model.old_password, model.password):
                
                error_msg = 'Incorrect password.'
                form.old_password.errors.append(error_msg)
                raise ValidationError(error_msg)

            model.password = hash_password(model.new_password)
            model.fs_uniquifier = uuid.uuid4().hex

        super().on_model_change(form, model, is_created)

        if issubclass(self.model, GranularAccessMixin) \
                and getattr(form, 'use_unique_access', False) \
                and not model.has_unique_access \
                and model.access_node != model.get_model_access_node():

            self_access = UserAccess(
                access=model.access_node,
                user=model,
                role=Role.get_by_name(CONTRIBUTOR)
            )
            self.session.add(self_access)


class GroupsAdmin(AdminAccessModelView):
    """Admin view for model Group."""

    model = Group

    column_list = ('name', 'created_at', 'updated_at',)
    column_filters = column_list
    column_searchable_list = ('name', 'description',)
    form_extra_fields = {
        'use_unique_access': BooleanField('Use Unique Access?'),
    }
    form_columns = (
        'uuid',
        'created_at',
        'updated_at',
        'access_node',
        'use_unique_access',
        'name',
        'description',
        'users',
    )
    column_details_list = form_columns
    form_create_rules = exclude(form_columns, ('uuid',
            'created_at', 'updated_at',))
    form_edit_rules = form_create_rules


class UserAccessesAdmin(AdminAccessModelView):

    model = UserAccess
    
    can_edit = False
    column_list = ('access', 'user', 'role',)
    column_filters = column_list
    column_searchable_list = (
        'access.name',
        'user.username',
        'user.email',
        'role.name',
    )
    form_columns = (
        'uuid',
        'created_at',
        'updated_at',
        'access',
        'user',
        'role',
    )
    column_details_list = form_columns


class GroupAccessesAdmin(AdminAccessModelView):

    model = GroupAccess
    
    can_edit = False
    column_list = ('access', 'group', 'role',)
    column_filters = column_list
    column_searchable_list = (
        'access.name',
        'group.name',
        'role.name',
    )
    form_columns = (
        'uuid',
        'created_at',
        'updated_at',
        'access',
        'group',
        'role',
    )
    column_details_list = form_columns
