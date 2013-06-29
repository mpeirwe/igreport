import re
import json
import locale
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.forms import ModelForm, ModelChoiceField
from rapidsms_httprouter.models import Message
from rapidsms.contrib.locations.models import Location
from igreport.models import Report, IGReport, Currency, UserProfile, Category, MessageLog, Unprocessed
from igreport.models import DNDList
from igreport import util, media
from igreport.html.admin import ListStyleAdmin
from igreport.report_admin import ReportAdmin
from igreport.unregister import unregister_apps

class DNDListAdmin(admin.ModelAdmin):
    list_display = ['msisdn', 'notes_', 'date', 'updated_']

    def date(self, obj):
        return obj.entry_date.strftime('%d/%m/%Y %H:%M')

    date.short_description = 'Entry Date'
    date.admin_order_field = 'entry_date'

    def updated_(self, obj):
        return obj.updated.strftime('%d/%m/%Y %H:%M')

    updated_.short_description = 'Updated'
    updated_.admin_order_field = 'updated'
    
    def notes_(self, obj):
        return util.truncate_str(obj.notes, 50)
    
class IGReportAdmin(admin.ModelAdmin, ListStyleAdmin):

    list_display = ['sender', 'message', 'accused', 'amount_formatted', 'refno', 'report_time', 'options']
    list_filter = ['datetime']
    ordering = ['-datetime']
    date_hierarchy = 'datetime'
    search_fields = ['connection__identity', 'reference_number']
    actions = None
    Media = media.JQueryUIMedia
    change_list_template = 'igreport/change_list.html'
    change_list_results_template = 'igreport/change_list_results.html'
    list_per_page = 50

    def __init__(self, *args, **kwargs):
        super(IGReportAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = (None,)

    def report_time(self, obj):
        return obj.datetime.strftime('%d/%m/%Y %H:%M')

    report_time.short_description = 'Report Date'
    report_time.admin_order_field = 'datetime'

    def message(self, obj):
        text = obj.report
        width = ''
        if text and len(text) > 40:
            width = '280px'

        style = 'font-size:13px;'
        if width:
            style += 'width:%s;' % width
        if style:
            style = ' style="%s"' % style
        html = '<div id="rpt_%s"%s>%s</div>' % (obj.id, style, text)
        return html

    message.short_description = 'Report'
    message.allow_tags = True

    def accused(self, obj):
        text = obj.subject
        width = ''
        if text and len(text) > 40:
            width = '200px'

        style = 'font-size:13px;'
        if width:
            style += 'width:%s;' % width
        if style:
            style = ' style="%s"' % style
        if not text:
            text = '<span style="color:#cc0000">(none)</span>'
        html = '<div%s>%s</div>' % (style, text)
        return html

    accused.short_description = 'Accused'
    accused.allow_tags=True

    def sender(self, obj):
        msisdn = obj.connection.identity
        t = (msisdn, msisdn, msisdn)
        html = '<a href="../unprocessed/?q=%s" \
               style="font-weight:bold" title="Click to view unprocessed messages from %s">%s</a>' % t
        return html
    
    sender.short_description = 'Sender'
    sender.admin_order_field = 'connection'
    sender.allow_tags = True

    def amount_formatted(self, obj):
        if obj.amount:
            amount = int(obj.amount)
            locale.setlocale(locale.LC_ALL, '')
            amount = locale.format("%d", amount, grouping=True)
            currency = ''
            if obj.currency:
                currency = obj.currency.code
            amount = '<span style="color:#cc0000;font-weight:bold">%s</span>' % amount
            if currency:
                amount = '%s%s' % (currency, amount)
            return amount
        return 'NA'
    
    amount_formatted.short_description = 'Amount'
    amount_formatted.admin_order_field = 'amount'
    amount_formatted.allow_tags=True

    def refno(self, obj):
        if not obj.reference_number:
            return '__'

        return obj.reference_number
    
    refno.short_description = 'Ref. No'
    refno.admin_order_field = 'reference_number'

    def options(self, obj):
        html = ''
        if not obj.synced and not obj.closed:
            link = '<a href="" onclick="editrpt(%s);return false;" title="Edit Report"><img src="%s/igreport/img/edit.png" border="0" /></a>&nbsp;&nbsp;' % (obj.id, settings.STATIC_URL)
            html += link
            
        link = '<a href="/igreports/%s/print/igreport/" title="Print Report" target="_blank"><img src="%s/igreport/img/print.png"></a><br/>' % (obj.id, settings.STATIC_URL)
        html += link
        
        html = '<div style="padding-bottom:5px">%s</div>' % html

        if obj.completed and not obj.synced and not obj.closed:
            d = dict(id=str(obj.id), amount=str(obj.amount) if obj.amount else '', amountff=obj.amount_freeform or '')
            a = json.dumps( d )
            if re.search("'", a):
                a = re.compile("'").sub("", a)
            link = '<a href="" onclick=\'syncit(%s);return false;\' title="Sync Report"><img src="%s/igreport/img/sync.png"></a>&nbsp;&nbsp;' % (a, settings.STATIC_URL)
            html += link
        
        msisdn = obj.connection.identity
        t = (msisdn, obj.id, msisdn, settings.STATIC_URL)
        html += '<a href="" title="Send SMS to %s" onclick="smsp(%s,\'%s\',\'report\');return false;"><img src="%s/igreport/img/sms.png" border="0" /></a>' % t

        return html

    options.short_description = 'Options'
    options.allow_tags = True
    
    def get_row_css(self, obj, index):
        if obj.completed:
            return ' rpt-completed'
        if obj.synced:
            return ' rpt-synced'
        return ''

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def change_view(self, request, object_id, extra_context=None):
        raise PermissionDenied
    
    def changelist_view(self, request, extra_context=None):
        title = 'Reports'
        
        ids = [ '{id:%s,completed:%s,synced:%s,closed:%s}' % \
               (obj.id, 'true' if obj.completed else 'false', \
                'true' if obj.synced else 'false', 'true' if obj.closed else 'false') \
        for obj in self.queryset(self) ]
        js = '[%s]' % ','.join(ids)
        bottom_js = '\nvar reports=%s;\nrptsetc();\n' % js
        
        #bottom_js=''
        buttons = [ dict(label='Refresh', link=''), dict(label='All Reports', link='?'), dict(label='Completed', link='?completed=1'), dict(label='Synced', link='?synced=1'), dict(label='Closed', link='?closed=1') ]
        context = dict(title=title, include_file='igreport/report.html', bottom_js=bottom_js, buttons=buttons)
        return super(IGReportAdmin, self).changelist_view(request, extra_context=context)

class MessageLogAdmin(admin.ModelAdmin):
    list_display = ['sender', 'message', 'send_date', 'direction', 'status', 'options']
    search_fields = ('connection__identity', 'text')
    list_filter = ['date', 'direction', 'status']
    actions = None
    date_hierarchy = 'date'
    Media = media.JQueryUIMedia
    change_list_template = 'igreport/change_list.html'
    Media = media.JQueryUIMedia
    
    def __init__(self, *args, **kwargs):
        super(MessageLogAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = (None,)
        
    def sender(self, obj):
        return obj.connection.identity
    
    sender.admin_order_field = 'connection'

    def message(self, obj):
        text = obj.text
        if obj.direction == 'I':
            color='#336699'
        else:
            color = '#000'
        width = ''
        if len(text) > 50:
            width = '300px'

        style = 'color:%s;font-size:13px;' % color
        if width:
            style += 'width:%s;' % width
        if style:
            style = ' style="%s"' % style
        html = '<div id="rpt_%s"%s>%s</div>' % (obj.id, style, text)
        
        if obj.direction == 'I':
            html += '<div style="padding-top:7px"><a href="" onclick="create_report(%s,\'%s\');return false;" style="color:#999">[Create Report]</a></div>' % (obj.id, obj.connection.identity)
        return html
    
    message.allow_tags='True'

    def send_date(self, obj):
        return obj.date.strftime('%d/%m/%Y %H:%M')

    send_date.short_description = 'Send Date'
    send_date.admin_order_field = 'date'

    def options(self, obj):
        if obj.direction=='I':
            msisdn = obj.connection.identity
            t = (msisdn, obj.id, msisdn, settings.STATIC_URL)
            links = list()
            links.append( '<a href="" title="Send SMS to %s" onclick="smsp(%s,\'%s\',\'log\');return false;"><img src="%s/igreport/img/sms.png" border="0" /></a>' % t)
            
            #t = (obj.id, settings.STATIC_URL)
            #links.append( '<a href="" onclick="create_report(%s);return false;"><img src="%s/igreport/img/createreport.png"/></a>' % t)
            html = '&nbsp;'.join(links)
        else:
            html = '<span style="color:#ccc">[NONE]</span>'
        return html

    options.short_description = 'Options'
    options.allow_tags = True
    
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):

        buttons = [ {'label': 'Go To Reports', 'link': '../igreport/'}, {'label': 'Refresh', 'link': '?'} ]
        context = dict(title='All Messages', buttons=buttons, include_file='igreport/report.html')
        return super(MessageLogAdmin, self).changelist_view(request, extra_context=context)
    
    def change_view(self, request, object_id, extra_context=None):
        raise PermissionDenied

class UnprocessedAdmin(admin.ModelAdmin):
    list_display = ['sender', 'message', 'send_date']
    date_hierarchy = 'date'
    search_fields = ('connection__identity', 'text')
    list_filter = ['date']
    actions = None
    change_list_template = 'igreport/change_list.html'

    def __init__(self, *args, **kwargs):
        super(UnprocessedAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = (None,)
        
    def sender(self, obj):
        return obj.connection.identity
    
    sender.admin_order_field = 'connection'

    def message(self, obj):
        text = obj.text
        
        width = ''
        if len(text) > 50:
            width = '300px'
            
        style = 'font-size:13px;'
        if width:
            style += 'width:%s;' % width
        if style:
            style = ' style="%s"' % style
        html = '<div id="rpt_%s"%s>%s</div>' % (obj.id, style, text)
        return html
    
    message.allow_tags='True'

    def send_date(self, obj):
        return obj.date.strftime('%d/%m/%Y %H:%M')

    send_date.short_description = 'Send Date'
    send_date.admin_order_field = 'date'
    
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):

        buttons = [ {'label': 'Go To Reports', 'link': '../igreport/'}, {'label': 'Refresh', 'link': '?'} ]
        context = {'title': 'Unprocessed Messages', 'buttons': buttons}
        return super(UnprocessedAdmin, self).changelist_view(request, extra_context=context)
    
    def change_view(self, request, object_id, extra_context=None):
        raise PermissionDenied
    
    def queryset(self, request):
        qs = super(UnprocessedAdmin, self).queryset(request)
        return qs.filter(direction='I', application=None)

class UserProfileForm(ModelForm):
    district = ModelChoiceField(Location.objects.filter(type__name='district').order_by('name'))
    class Meta:
        model = UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    form = UserProfileForm

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']

class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']

admin.site.register(Report, ReportAdmin)    
admin.site.register(IGReport, IGReportAdmin)
admin.site.register(Currency, CurrencyAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(MessageLog, MessageLogAdmin)
admin.site.register(Unprocessed, UnprocessedAdmin)
admin.site.register(DNDList, DNDListAdmin)

unregister_apps()
