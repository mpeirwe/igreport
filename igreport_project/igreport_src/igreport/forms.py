# vim: ai ts=4 sts=4 et sw=4
# encoding=utf-8
import re
import datetime
from django import forms
from igreport import util, log
from igreport.models import IGReport, BulkMessage

class IGReportForm(forms.ModelForm):
    class Meta:
        model = IGReport

class BulkMessageForm(forms.ModelForm):
    
    class Meta:
        model = BulkMessage
        
    message = forms.CharField(label='SMS Message', widget=forms.Textarea(attrs={'cols':'60','rows':'6', 'onkeyup':'track_msg_len(this)', 'onblur':'track_msg_len(this)','onfocus':'track_msg_len(this)'}), \
        error_messages={'required':(u'Specify a valid text message')}, \
        help_text='The SMS message to send')
    
    recipients = forms.CharField(label='Recipients', required=False, \
        widget=forms.Textarea(attrs={'cols':'60','rows':'6'}),
        help_text='Specify phone numbers to which the message should be sent. \
        The numbers MUST be in internation format.<br/>Example <strong>2567121234567</strong>')

    recipients_file = forms.FileField(label='Recipients File', required=False, max_length=60, \
        help_text='Upload an excel file containing a list of phone numbers. \
        The first row in the excel file will be assumed to contain the \
        title and will be ignored')

    def clean_send_time(self):
        send_time = self.cleaned_data['send_time']
        if self.is_valid():
            now = datetime.datetime.now()
            
            if send_time < now:
                raise forms.ValidationError('Send time must be not be in the past')
        
        return send_time

    def clean_file(self):
        f = self.cleaned_data['recipients_file']
        if self.is_valid():
            if f and not re.search('excel|octet-stream', f.content_type, re.IGNORECASE):
                raise ValidationError('"%s" is not a valid Excel file. \
                    File type is %s' % (f.name, f.content_type))
        return f
    
    def clean(self):
        instance = getattr(self, 'instance', None)
        if instance.pk and instance.status != 'PENDING':
            raise forms.ValidationError('This message is not in \
                PENDING state and can not be modified')
        
        if self.is_valid():
            recipients_text = self.cleaned_data['recipients']
            recipients = list()
            res = util.import_contacts_from_xls_file(self.request, self)
            if res['error']:
                raise forms.ValidationError(res['message'])
            
            if res['result']:
                recipients = recipients + res['result']
                
            if recipients_text:
                tokens = re.compile(r',|\s+|\n+', re.IGNORECASE).split(recipients_text)
                for number in tokens:
                    if not number: continue
                    if not re.search('^256[0-9]{9}$', number):
                        raise forms.ValidationError('Invalid recipient "%s"' % number)
                    
                    recipients.append(number)
            
            if not recipients and not instance.pk:
                raise forms.ValidationError('Specify at least one message recipient')
            
            self.request.POST['recipient_list'] = recipients
    
        return super(BulkMessageForm, self).clean()