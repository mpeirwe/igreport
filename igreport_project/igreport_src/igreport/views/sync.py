#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
# encoding=utf-8

import logging
import urllib2
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from igreport.models import IGReport
from rapidsms_httprouter.models import Message
from django.utils import simplejson
from django.conf import settings
from igreport import responses
from igreport.models import Comment
from datetime import date, datetime
from django.utils.encoding import smart_str

log = logging.getLogger(__name__)

@require_POST
@login_required
def sync_report(request, report_id):
    report = get_object_or_404(IGReport, pk=long(report_id))
    # username
    # password

    # accused
    # accused_gender
    # district
    # report, offences
    # !complainant should not be anonymous
    # !dupes must be handled on cms
    # !report vs. offences?
    # !category? date? phone number? comments?
    # no security (and key errors for missing username/pass)

    # {"accused":"blah",
    #  "accused_gender":"M",
    #  "accused_ent_type":"P",
    #  "district":"kampala",
    #  "report":"test",
    #  "offences":"test",
    #  "username":"admin",
    #  "password":"admin"}
    if not report.completed:
        return HttpResponse('Report incomplete', status=400)
    
    report_data = None
    json_response = None
    
    try:
        report_data = { \
            'accused': smart_str(report.subject),
            'accused_gender': 'N',  # don't collect gender
            'accused_ent_type': 'P',  # don't collect type
            'district': report.district.name,
            'offences': ','.join(report.categories.values_list('name', flat=True)),
            'username': settings.CMS_USER,
            'password': settings.CMS_PASSWORD,
            'complainant': report.connection.identity,
            'complainant_names': report.names if report.names else '',
            'report': smart_str(report.report),
            'what_was_involved': smart_str(report.amount_freeform), 
            'reference_number': smart_str(report.reference_number),
            'complaint_date': datetime.strftime(report.datetime, '%Y/%m/%d'),
        }
        if report.amount > 0:
            report_data['amount'] = report.amount

        qs = Comment.objects.filter(report=report)
        comments = list()
        for c in qs:
            if not c.comment: continue
            comments.append(c.comment)
        if comments:
            report_data['comments'] = comments

        report_data = simplejson.dumps(report_data)
        
        cms_url = settings.CMS_URL
        req = urllib2.Request(cms_url, report_data)
        response = urllib2.urlopen(req)
        json_response = response.read()
        json_object = simplejson.loads(json_response)
        
        if (json_object['result'] != 'OK'):
            log.info('DATA [[ %s ]] RESPONSE [[ %s ]]' % (report_data, json_response))
            return HttpResponse(json_object['message'], status={'PD':403, 'RC':404, 'IE':500}[json_object['result']])

        report.synced = True
        report.save()
        
        # send user response
        translations = responses.translations
        lang = report.connection.contact.language
        if translations.has_key(lang):
            response = translations[lang]
            if response.has_key('SYNC_RESPONSE_MESSAGE'):
                text = response['SYNC_RESPONSE_MESSAGE'] % {'reference_number':report.reference_number}
                Message.objects.create(direction='O', status='Q', \
                connection=report.connection, text=text, application='igreport')
                
        return HttpResponse('OK', status=200)
    except Exception as err:
        log.exception(err.__str__())
        log.info('DATA [[ %s ]] RESPONSE [[ %s ]]' % (report_data, json_response))
        return HttpResponse(err.__str__(), status=500)
