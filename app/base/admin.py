from ..auth.admin import (
    AdminAccessModelView,
)
from ..core.utils import exclude
from .models import (
    Ministry,
    Person,
    SitePage,
)


class PeopleAdmin(AdminAccessModelView):

    model = Person

    column_list = (
        'prefix',
        'first_name',
        'middle_name',
        'last_name',
        'postfix',
    )
    column_filters = column_list
    column_searchable_list = (
        'prefix',
        'first_name',
        'middle_name',
        'last_name',
        'postfix',
        'nickname',
    )
    form_columns = (
        'uuid',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
        'access_node',
        'use_unique_access',
        'prefix',
        'first_name',
        'middle_name',
        'last_name',
        'postfix',
        'birthday',
        'user',
    )
    form_create_rules = (
        'access_node',
        'use_unique_access',
        'prefix',
        'first_name',
        'middle_name',
        'last_name',
        'postfix',
        'birthday',
        'user',
    )
    form_edit_rules = form_create_rules


class SitePagesAdmin(AdminAccessModelView):

    model = SitePage

    column_list = ('url_title', 'title', 'active',)
    column_filters = column_list
    column_searchable_list = column_list
    form_columns = (
        'uuid',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
        'access_node',
        'use_unique_access',
        'url_title',
        'title',
        'template_name',
        'active',
    )
    form_create_rules = (
        'access_node',
        'use_unique_access',
        'url_title',
        'title',
        'template_name',
        'active',
    )
    form_edit_rules = form_create_rules


class MinistriesAdmin(AdminAccessModelView):

    model = Ministry

    column_list = ('name', 'short_description',)
    column_filters = ('name',)
    column_searchable_list = ('name', 'short_description', 'description',)
    form_columns = (
        'uuid',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
        'access_node',
        'use_unique_access',
        'name',
        'short_description',
        'description',
        'logo_url',
    )
    form_create_rules = (
        'access_node',
        'use_unique_access',
        'name',
        'short_description',
        'description',
        'logo_url',
    )
    form_edit_rules = form_create_rules
