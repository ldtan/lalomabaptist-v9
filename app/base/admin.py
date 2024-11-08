from typing import Any, Tuple
from flask import flash
from flask_admin.actions import action
from flask_admin.babel import (
    gettext,
    ngettext,
)
from flask_admin.form.fields import Select2Field
from flask_security import current_user
from pytubefix import YouTube

from ..auth.admin import (
    AdminAccessModelView,
)
from ..auth.constants import Permission
from ..core.admin import (
    CKTextAreaField,
    Select2MultipleField,
)
from ..core.utils import exclude
from .models import (
    BulletinPost,
    Event,
    Ministry,
    Person,
    PrayerRequest,
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

    def _activate_record(self, record, flag: bool = True) -> Tuple[Any, bool]:
        has_permission = record.access_node.has_user_permissions(
                current_user, Permission.EDIT_RECORD)

        if has_permission:
            record.active = flag
            self.session.commit()

        return record, has_permission
    
    @action('enable', 'Enable', 'Are you sure you want to enable the selected pages?')
    def action_enable(self, ids):
        try:
            updated_records = self.update_records(
                ids,
                lambda r: self._activate_record(r, True),
            )
            count = len(updated_records)

            flash(
                ngettext(
                    'Record was successfully enabled.',
                    f"{count} records were successfully enabled.",
                    count,
                    count=count,
                ),
                'success',
            )
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise

            flash(gettext('Failed to enable records. %(error)s', error=str(ex)), 'error')
    
    @action('disable', 'Disable', 'Are you sure you want to disable the selected pages?')
    def action_disable(self, ids):
        try:
            updated_records = self.update_records(
                ids,
                lambda r: self._activate_record(r, False),
            )
            count = len(updated_records)

            flash(
                ngettext(
                    'Record was successfully disabled.',
                    f"{count} records were successfully disabled.",
                    count,
                    count=count,
                ),
                'success',
            )
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise

            flash(gettext('Failed to disable records. %(error)s', error=str(ex)), 'error')


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
    column_default_sort = [('start_datetime', True),]
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
        'preacher',
        'video_url',
        'thumbnail_url',
        'outline_url',
    )
    column_details_list = exclude(form_columns, ['use_unique_access'])
    form_create_rules = (
        'access_node',
        'use_unique_access',
        'title',
        'description',
        'start_datetime',
        'preacher',
        'video_url',
        'thumbnail_url',
        'outline_url',
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


class PrayerRequestsAdmin(AdminAccessModelView):

    model = PrayerRequest
    
    column_list = ('title', 'description', 'status',)
    column_filters = column_list
    column_searchable_list = ('title', 'description', 'status',)
    form_args = {
        'status': {'choices': PrayerRequest.STATUS_CHOICES},
    }
    form_overrides = {
        'status': Select2Field,
        'updates': CKTextAreaField,
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
        'description',
        'status',
        'people_praying',
        'updates',
    )
    column_details_list = exclude(form_columns, ['use_unique_access'])
    form_create_rules = (
        'access_node',
        'use_unique_access',
        'title',
        'description',
        'status',
        'people_praying',
        'updates',
    )
    form_edit_rules = form_create_rules
