# vim: ai ts=4 sts=4 et sw=4
# encoding=utf-8
from django.contrib import admin
from igreport.models import *
from igreport import util, log
from igreport import media

class DistrictAdmin(admin.ModelAdmin):
    list_display = ['district']
    search_fields = ['name']
    actions = ['delete_districts']
    Media = media.JQueryUIMedia
    list_per_page = 20
    change_list_template = 'igreport/change_list.html'

    def __init__(self, *args, **kwargs):
        super(DistrictAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = (None,)

    def district(self, obj):
        a = '<a href="" onclick="adp(%s,\'%s\');return false;">%s</a>' % (obj.id, obj.name, obj.name)
        
        return a
    
    district.allow_tags = True
    district.admin_order_field = 'name'
    
    def queryset(self, request):
        qs = super(DistrictAdmin, self).queryset(request)
        return qs.filter(type='district')

    # XXX: If Deleting is allowed, do not delete
    # district which as a case associated with it
    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        raise PermissionDenied

    def get_actions(self, request):
        actions = super(DistrictAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions
    
    def delete_districts(self, request, queryset):
        for district in queryset:
            # XXX: Very reluctant to implement this
            # as it will delete associated reports ..
            log.info('Will not delete district "%s"' % district.name)
            
    delete_districts.short_description ='Delete Districts'
    
    def changelist_view(self, request, extra_context=None):

        buttons = [ dict(label='Add District', link='', js=' onclick="adp(0,\'\');return false;"'), dict(label='Refresh', link='',) ]
        context = dict(title='Districts', buttons=buttons, include_file='igreport/report.html')
        
        return super(DistrictAdmin, self).changelist_view(request, extra_context=context)