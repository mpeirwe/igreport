# vim: ai ts=4 sts=4 et sw=4
# encoding=utf-8
import locale
from django.contrib import admin
from django.conf import settings
from igreport import util, media
from django.core.exceptions import PermissionDenied
from igreport.models import Report

class ReportAdmin(admin.ModelAdmin):

    list_display = ['sender', 'message', 'accused', 'amount_formatted', 'report_time', 'options']
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
        super(ReportAdmin, self).__init__(*args, **kwargs)
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

    def options(self, obj):

        html = '<a href="/igreports/%s/print/report/" target="_blank">Details</a> | <a href="/igreports/%s/accept/" onclick="return confirm(\'Accept report?\')">Accept</a>' % (obj.id, obj.id)

        return html

    options.short_description = 'Options'
    options.allow_tags = True
    
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def change_view(self, request, object_id, extra_context=None):
        raise PermissionDenied
    
    def changelist_view(self, request, extra_context=None):
        title = 'Pending Reports'
        
        ids = [ '{id:%s,completed:%s,synced:%s,closed:%s}' % \
               (obj.id, 'true' if obj.completed else 'false', \
                'true' if obj.synced else 'false', 'true' if obj.closed else 'false') \
        for obj in self.queryset(self) ]
        js = '[%s]' % ','.join(ids)
        bottom_js = '\nvar reports=%s;\nrptsetc();\n' % js
        
        #bottom_js=''
        buttons = [ dict(label='Refresh', link=''), ]
        context = dict(title=title, include_file='igreport/report.html', bottom_js=bottom_js, buttons=buttons)
        return super(ReportAdmin, self).changelist_view(request, extra_context=context)