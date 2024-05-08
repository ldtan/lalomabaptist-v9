from flask_admin.form.fields import Select2Field
from pytube import YouTube

from ..auth.admin import (
    AdminAccessModelView,
)
from ..core.admin import Select2MultipleField
from ..core.utils import exclude
from .models import (
    BulletinPost,
    Event,
    Ministry,
    Person,
    Preaching,
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
        'created_by',
        'updated_at',
        'updated_by',
        'access_node',
        'use_unique_access',
        'prefix',
        'first_name',
        'middle_name',
        'last_name',
        'postfix',
        'nickname',
        'birthday',
        'user',
    )
    column_details_list = exclude(form_columns, ['use_unique_access'])
    form_create_rules = (
        'access_node',
        'use_unique_access',
        'prefix',
        'first_name',
        'middle_name',
        'last_name',
        'postfix',
        'nickname',
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
        'created_by',
        'updated_at',
        'updated_by',
        'access_node',
        'use_unique_access',
        'url_title',
        'title',
        'template_name',
        'active',
    )
    column_details_list = exclude(form_columns, ['use_unique_access'])
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
        'created_by',
        'updated_at',
        'updated_by',
        'access_node',
        'use_unique_access',
        'name',
        'short_description',
        'description',
        'logo_url',
    )
    column_details_list = exclude(form_columns, ['use_unique_access'])
    form_create_rules = (
        'access_node',
        'use_unique_access',
        'name',
        'short_description',
        'description',
        'logo_url',
    )
    form_edit_rules = form_create_rules


class PreachingsAdmin(AdminAccessModelView):

    model = Preaching

    column_list = ('title', 'preacher', 'start_datetime',)
    column_filters = column_list
    column_searchable_list = ('title', 'preacher.full_name', 'description',)
    form_columns = (
        'uuid',
        'created_at',
        'created_by',
        'updated_at',
        'updated_by',
        'access_node',
        'use_unique_access',
        'title',
        'description',
        'start_datetime',
        'video_url',
        'thumbnail_url',
        'preacher',
    )
    column_details_list = exclude(form_columns, ['use_unique_access'])
    form_create_rules = (
        'access_node',
        'use_unique_access',
        'title',
        'description',
        'start_datetime',
        'video_url',
        'thumbnail_url',
        'preacher',
    )
    form_edit_rules = form_create_rules

    def on_model_change(self, form, model, is_created):
        super().on_model_change(form, model, is_created)

        if model.thumbnail_url is None and model.video_url:
            try:
                yt_video = YouTube(model.video_url)
                model.thumbnail_url = yt_video.thumbnail_url
            except:
                pass


class EventsAdmin(AdminAccessModelView):

    model = Event

    column_list = ('title', 'short_description', 'venue', 'start_datetime',)
    column_filters = column_list
    column_searchable_list = ('title', 'short_description', 'venue',)
    # form_args = {
    #     'repeat': {'choices': Event.REPEAT_CHOICES},
    #     'repeat_on': dict(
    #         render_kw={'multiple': 'multiple'},
    #         choices=Event.REPEAT_ON_CHOICES,
    #     ),
    # }
    # form_overrides = {
    #     'repeat': Select2Field,
    #     'repeat_on': Select2MultipleField,
    # }
    form_columns = (
        'uuid',
        'created_at',
        'created_by',
        'updated_at',
        'updated_by',
        'access_node',
        'use_unique_access',
        'title',
        'short_description',
        'description',
        'venue',
        'start_datetime',
        'end_datetime',
        # 'repeat',
        # 'repeat_on',
        'include_time',
    )
    column_details_list = exclude(form_columns, ['use_unique_access'])
    form_create_rules = (
        'access_node',
        'use_unique_access',
        'title',
        'short_description',
        'description',
        'venue',
        'start_datetime',
        'end_datetime',
        # 'repeat',
        # 'repeat_on',
        'include_time',
    )
    form_edit_rules = form_create_rules


class BulletinPostsAdmin(AdminAccessModelView):

    model = BulletinPost

    column_list = ('title', 'content', 'source', 'pinned_until',)
    column_filters = column_list
    column_searchable_list = ('title', 'content', 'source',)
    form_args = {
        'image_position': {'choices': BulletinPost.IMAGE_POSITION_CHOICES},
        'display': dict(
            render_kw={'multiple': 'multiple'},
            choices=BulletinPost.DISPLAY_CHOICES,
        ),
    }
    form_overrides = {
        'image_position': Select2Field,
        'display': Select2MultipleField,
    }
    form_columns = (
        'uuid',
        'created_at',
        'created_by',
        'updated_at',
        'updated_by',
        'access_node',
        'use_unique_access',
        'title',
        'content',
        'source',
        'image_url',
        'image_position',
        'display',
        'pinned_until',
    )
    column_details_list = exclude(form_columns, ['use_unique_access'])
    form_create_rules = (
        'access_node',
        'use_unique_access',
        'title',
        'content',
        'source',
        'image_url',
        'image_position',
        'display',
        'pinned_until',
    )
    form_edit_rules = form_create_rules
