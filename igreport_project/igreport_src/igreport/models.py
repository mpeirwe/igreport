#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
# encoding=utf-8

from django.db import models
from django.contrib.auth.models import User
from rapidsms.models import Connection
from rapidsms.contrib.locations.models import Location
from script.signals import script_progress_was_completed
from .signal_handlers import handle_report, igreport_pre_save#, igreport_msgq_pre_save
from django.db.models.signals import pre_save
from rapidsms_httprouter.models import Message
from rapidsms_httprouter.models import mass_text_sent

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    district = models.ForeignKey(Location, null=True, default=None)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

class Category(models.Model):
    name = models.TextField()
    description = models.TextField()

    class Meta:
        verbose_name = 'Report Category'
        verbose_name_plural = 'Report Categories'

class Comment(models.Model):
    report = models.ForeignKey('IGReport', related_name='comments')
    user = models.ForeignKey(User, null=True, default=None)
    datetime = models.DateTimeField(auto_now_add=True)
    comment = models.TextField()

class Currency(models.Model):
    code = models.CharField('Code', max_length=3, unique=True, help_text='The currency code, E.g UGX')
    name = models.CharField('Name', max_length=100, help_text='The currency name, E.g Uganda Shillings')
    
    class Meta:
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'

class Report(models.Model):
    connection = models.ForeignKey(Connection)
    completed = models.BooleanField(default=False)
    synced = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)
    datetime = models.DateTimeField(auto_now_add=True, verbose_name='Report Date')
    reference_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    keyword = models.TextField(blank=True, null=True, default=None)
    report = models.TextField()
    subject = models.TextField(blank=True, null=True, default=None)
    district_freeform = models.TextField(null=True, blank=True)
    district = models.ForeignKey(Location, null=True, default=None)
    amount_freeform = models.TextField(null=True, blank=True)
    amount = models.DecimalField(decimal_places=2, max_digits=26, null=True)
    currency = models.ForeignKey(Currency, null=True, blank=True)
    names = models.TextField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pending Report'
        verbose_name_plural = 'Pending Reports'

class IGReport(models.Model):
    connection = models.ForeignKey(Connection)
    completed = models.BooleanField(default=False)
    synced = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)
    datetime = models.DateTimeField(auto_now_add=True, verbose_name='Report Date')
    reference_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    keyword = models.TextField(blank=True, null=True, default=None)
    report = models.TextField()
    subject = models.TextField(blank=True, null=True, default=None)
    district_freeform = models.TextField(null=True, blank=True)
    district = models.ForeignKey(Location, null=True, default=None, related_name='district_reports')
    categories = models.ManyToManyField(Category, related_name='reports')
    amount_freeform = models.TextField(null=True, blank=True)
    amount = models.DecimalField(decimal_places=2, max_digits=26, null=True)
    currency = models.ForeignKey(Currency, null=True, blank=True)
    names = models.TextField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'

class DNDList(models.Model):
    entry_date = models.DateTimeField('Entry Date', auto_now_add=True)
    msisdn = models.CharField('Phone Number', max_length=15, primary_key=True, help_text='The phone number to which messages should not be sent. Number should be in international format, E.g 256712123456')
    notes = models.CharField('Notes', max_length=255, help_text='Notes about this entry')
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'DND Number'
        verbose_name_plural = 'DND Numbers'

class BulkMessage(models.Model):
    entry_date = models.DateTimeField('Entry Date', auto_now_add=True)
    message = models.TextField('Message', help_text='The SMS message to send')
    status = models.CharField('Status', max_length=20, default='PENDING', editable=False, \
        choices=(('PENDING','PENDING'),('PROCESSING','PROCESSING'),('SENT','SENT'), ('CANCELED','CANCELED')))
    send_time = models.DateTimeField('Send Time', help_text='Specify the date/time when this message will be sent')
    notes = models.CharField('Notes', max_length=255, null=True, blank=True, help_text='Optional notes about this message')
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s (%s)' % (self.message, self.status)

    class Meta:
        verbose_name = 'Bulk Message'
        verbose_name_plural = 'Bulk Messages'
        
class BulkRecipient(models.Model):
    entry_date = models.DateTimeField('Entry Date', auto_now_add=True)
    msisdn = models.TextField('MSISDN', max_length=20)
    message = models.ForeignKey(BulkMessage, editable=False)
    status = models.CharField('Status', max_length=20, default='PENDING', editable=False, \
        choices=(('PENDING','PENDING'),('SENT','SENT')))    
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Recipient'
        verbose_name_plural = 'Recipients'
        unique_together = ('msisdn', 'message')
    
class Unprocessed(Message):
    class Meta:
        proxy = True
        verbose_name = 'Unprocessed Message'
        verbose_name_plural = 'Unprocessed Messages'

class MessageLog(Message):
    class Meta:
        proxy = True
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

def bulk_process(sender, **kwargs):
    messages = kwargs['messages']
    status = kwargs['status']
    if status == 'P':
        messages.filter(status='P').update(status='Q')

mass_text_sent.connect(bulk_process, weak=False)
        
script_progress_was_completed.connect(handle_report, weak=False)
pre_save.connect(igreport_pre_save, sender=IGReport, weak=False)
