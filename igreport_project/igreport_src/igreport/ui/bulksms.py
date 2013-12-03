# vim: ai ts=4 sts=4 et sw=4
# encoding=utf-8
from django.contrib import admin
from igreport.models import BulkMessage, BulkRecipient
from igreport import util, log
from igreport import media
from igreport.forms import BulkMessageForm

class BulkMessageAdmin(admin.ModelAdmin):
    list_display = ['entry_date_', 'message_', 'recipients', \
        'send_date', 'status_', 'notes_', 'options']
    list_filter = ['status', 'send_time', 'entry_date']
    actions = ['_delete_selected', 'cancel']
    Media = media.JQueryUIMedia
    form = BulkMessageForm

    def entry_date_(self, obj):
        return obj.entry_date.strftime('%d/%m/%Y %H:%M')

    entry_date_.short_description = 'Entry Date'
    entry_date_.admin_order_field = 'entry_date'

    def send_date(self, obj):
        return obj.send_time.strftime('%d/%m/%Y %H:%M')

    send_date.short_description = 'Send Time'
    send_date.admin_order_field = 'send_time'

    def updated_(self, obj):
        return obj.updated.strftime('%d/%m/%Y %H:%M')

    updated_.short_description = 'Updated'
    updated_.admin_order_field = 'updated'

    def message_(self, obj):
        html = '<div style="width:300px">%s</div>' % obj.message
        return html
    message_.allow_tags = True
    
    def notes_(self, obj):
        if not obj.notes:
            return '<span style="color:#ccc">NONE</span>'
        return util.truncate_str(obj.notes, 30)
    
    notes_.allow_tags = True

    def status_(self, obj):
        color = '#999'
        if obj.status == 'PROCESSING':
            color = '#ff6600'
        elif obj.status == 'SENT':
            color = '#008800'
        elif obj.status == 'CANCELED':
            color = '#ff0000'
        
        html = '<span style="color:%s">%s</span>' % (color, obj.status)
        return html
    
    status_.allow_tags = True
    status_.admin_order_field = 'status'

    def recipients(self, obj):
        qs = BulkRecipient.objects.filter(message=obj)
        return qs.count()
    
    def options(self, obj):
        html = '<a href="../bulkrecipient/?message__id=%s">Recipients</a>' % obj.id
        
        return html
    options.allow_tags = True
    
    def _delete_selected(self, request, queryset):
        try:
            for obj in queryset:
                if ['PROCESSING', 'SENT'].__contains__(obj.status):
                    log.warn('Will not delete message: %s' % obj)
                    continue
                obj.delete()
        except Exception as errr:
            log.exception()
    _delete_selected.short_description = 'Delete Selected Messages'

    def cancel(self, request, queryset):
        try:
            for obj in queryset:
                if ['SENT'].__contains__(obj.status):
                    log.warn('Will not cancel message: %s' % obj)
                    continue
                
                obj.status = 'CANCELED'
                obj.save()
        except Exception as errr:
            log.exception()
    cancel.short_description = 'Cancel Selected Messages'
    
    def get_actions(self, request):
        actions = super(BulkMessageAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions
            
    def get_form(self, request, *args, **kwargs):
        form = super(BulkMessageAdmin, self).get_form(request, *args, **kwargs)
        form.request = request
        return form

    def save_model(self, request, obj, form, change):
        
        res = super(BulkMessageAdmin, self).save_model(request, obj, form, change)

        if request.POST.has_key('recipient_list'):
            recipients = request.POST['recipient_list']
            for msisdn in recipients:
                try:
                    BulkRecipient.objects.get_or_create(
                            message = obj,
                            msisdn = msisdn,
                    )
                except Exception as err:
                    log.exception()
        return res
    
    def changelist_view(self, request, extra_context=None):
        context = {'title':'Bulk SMS Messages'}
        return super(BulkMessageAdmin, self).changelist_view(request, extra_context=context)
    
    def add_view(self, request, form_url='', extra_context=None):
        context={'bottom_js':'attach_counter("id_message");'}
        return super(BulkMessageAdmin, self).add_view(request, form_url='', extra_context=context)

class BulkRecipientAdmin(admin.ModelAdmin):
    list_display = ['entry_date_', 'msisdn', 'status_', 'updated_']
    list_filter = ['status', 'entry_date']
    search_fields = ['msisdn']

    def entry_date_(self, obj):
        return obj.entry_date.strftime('%d/%m/%Y %H:%M')

    entry_date_.short_description = 'Entry Date'
    entry_date_.admin_order_field = 'entry_date'

    def updated_(self, obj):
        return obj.updated.strftime('%d/%m/%Y %H:%M')

    updated_.short_description = 'Updated'
    updated_.admin_order_field = 'updated'

    def status_(self, obj):
        color = '#999'
        if obj.status == 'SENT':
            color = '#008800'
        
        html = '<span style="color:%s">%s</span>' % (color, obj.status)
        return html
    
    status_.allow_tags = True
    status_.admin_order_field = 'status'

    def get_model_perms(self, request):
        return {}

    def changelist_view(self, request, extra_context=None):
        buttons = [dict(label='Bulk Messages', link='../bulkmessage/'),
            dict(label='Refresh', link='')]
        context = {'title':'Bulk Message Recipients', 'buttons':buttons}
        return super(BulkRecipientAdmin, self).changelist_view(request, extra_context=context)