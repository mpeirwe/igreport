# vim: ai ts=4 sts=4 et sw=4
# encoding=utf-8
from django.core.management.base import BaseCommand
from rapidsms.models import Connection, Backend
from igreport.models import *
from igreport import log
from igreport.lib import sms

class Command(BaseCommand):

    def handle(self, *files, **options):
        try:
            # Load the DND List
            dndlist = [dnd.msisdn for dnd in DNDList.objects.all()]
            backend, created = Backend.objects.get_or_create(name='youganda', defaults={})
            qs = BulkMessage.objects.filter(status='PENDING')[:1]
            
            for msg in qs:
                self.send_message(msg, backend, dndlist)
                
        except Exception as err:
            log.exception()
            print err.__str__()
    
    def send_message(self, msg, backend, dndlist):
        try:
            # mark status as "PROCESSING"
            msg.status = 'PROCESSING'
            msg.save()
            
            recipients = BulkRecipient.objects.filter(
                message = msg,
                status = 'PENDING'
            )
            total = recipients.count()
            log.info('Sending [%s] to %s recipient(s) ..' % (msg.message, total))
            
            for recipient in recipients:
                # get Connection object
                connection, created = \
                Connection.objects.get_or_create(
                    identity = recipient.msisdn,
                    backend = backend,
                    defaults = {}
                )
                params = dict(connection=connection, text=msg.message)
                sms.send_sms(params, dndlist)
            
                # mark recipient status as "SENT"
                recipient.status = 'SENT'
                recipient.save()
            
            # mark message status as "SENT"
            msg.status = 'SENT'
            msg.save()
                
        except Exception as err:
            log.exception()
            print err.__str__()        

