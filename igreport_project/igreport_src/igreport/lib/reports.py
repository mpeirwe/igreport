# vim: ai ts=4 sts=4 et sw=4
# encoding=utf-8
from igreport import util
from django.db import transaction
from igreport.models import IGReport, Report
from igreport.questions import translations
from rapidsms_httprouter.models import Message

def accept_report(report_id):
    txn = False
    try:
        with transaction.commit_on_success():
            txn = True
            rpt = Report.objects.get(pk=report_id)
            report = IGReport(connection=rpt.connection, keyword=rpt.keyword)
            report.save()
            
            report.datetime = rpt.datetime
            report.connection = rpt.connection
            report.report = rpt.report
            report.subject = rpt.subject
            report.district_freeform = rpt.district_freeform
            report.district = rpt.district
            report.amount_freeform = rpt.amount_freeform
            report.amount = rpt.amount
            report.names = rpt.names
            report.reference_number = util.get_reference_number(report.id)
            report.save()
            
            connection = report.connection
            text = (translations[connection.contact.language]['CONFIRMATION_MESSAGE'] % \
            {'reference_number':report.reference_number})
            text += util.get_tagline(connection)
            
            rpt.delete()
            
            Message.objects.create(\
                direction='O', \
                status='Q', \
                connection=connection, \
                application='igreport', \
                text=text)
            
    except Report.DoesNotExist:
        return 'Not Found'
    except Exception as err:
        if txn: transaction.rollback()
        return err.__str__()
    
    return None