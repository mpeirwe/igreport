import re
import json
import datetime
import urllib, urllib2
from django.db.models import Q
from django.db import transaction
from django.utils import simplejson
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from rapidsms.contrib.locations.models import Location, LocationType
from rapidsms_httprouter.models import Message
from rapidsms.models import Connection, Backend
from django.conf import settings
from igreport.models import IGReport, Currency, Category, Comment, DNDList
from igreport import util, log
from igreport.lib import sms

def ajax_success(msg=None, js_=None):
    if msg is None:
        msg = 'OK'

    if js_ is None:
        js = '{error:false, msg:"%s"}' % msg
    else:
        js = '{error:false, msg:"%s", %s}' % (msg, js_)
    return HttpResponse(js, mimetype='text/plain', status=200)

def ajax_error(msg):
    js = dict(error=True, msg=msg)
    return HttpResponse(json.dumps(js), mimetype='text/plain', status=200)

@require_GET
@never_cache
@login_required
def create_report(request, message_id):
    txn = False
    try:
        message = get_object_or_404(Message, direction='I', pk=message_id)
        txn = True
        with transaction.commit_on_success():
            report = IGReport(
                connection=message.connection,
                report=message.text
            )
            report.save()
            
            report.datetime = message.date
            report.reference_number = util.get_reference_number(report.id)
            report.save()
            comment = 'Created from user SMS: %s' % message.text
            Comment.objects.create(report=report, user=request.user, comment=comment)
            return HttpResponse(report.reference_number, status=200)
    except Exception as err:
        if txn: transaction.rollback()
        return HttpResponse(err.__str__(), status=500)

    return ajax_success()

@login_required
@require_GET
@never_cache
def get_report(request, report_id):

    try:
        r = get_object_or_404(IGReport, pk=report_id)
        
        default_currency, created = Currency.objects.get_or_create(code=settings.DEFAULT_CURRENCY['code'], defaults=dict(name=settings.DEFAULT_CURRENCY['name']))

        js = dict(accused = r.subject or '', report = r.report or '', amount_ff = r.amount_freeform or '', amount = str(int(r.amount)) if r.amount>=0 else '', district_ff=r.district_freeform or '', district_id = r.district_id or  '', date = r.datetime.strftime('%d/%m/%Y %H:%M'), sender= r.connection.identity, names = r.names or '', currency_id=r.currency.id if r.currency else default_currency.id)
        js_rpt = simplejson.dumps(js)

        ''' get districts '''
        objs = Location.objects.filter(type='district').order_by('name')
        l = [ '{id:%s,name:%s}' % (d.id, json.dumps(d.name)) for d in objs ]
        l.insert(0, '{id:"",name:""}')
        js_districts = '[%s]' % ','.join(l)

        ''' get currencies '''
        objs = Currency.objects.all().order_by('name')
        l = [ '{id:%s,code:%s,name:%s}' % (d.id, json.dumps(d.code), json.dumps(d.name)) for d in objs ]
        l.insert(0, '{id:"",code:"",name:""}')
        js_currencies = '[%s]' % ','.join(l)

        ''' the selected categories '''
        curr_categories = [c.id for c in r.categories.all()]

        ''' all categories '''
        objs = Category.objects.all()
        l = list()

        for c in objs:
            checked='false'
            if curr_categories.__contains__(c.id):
                checked = 'true'
            l.append( '{id:%s,name:%s,checked:%s}' % (c.id, json.dumps(c.name), checked) )

        js_cat = '[%s]' % ','.join(l)

        ''' comments '''
        objs = Comment.objects.filter(report=r)
        l = [ '{user:%s,date:%s,comment:%s}' % (json.dumps(c.user.username), json.dumps(c.datetime.strftime('%d/%m/%Y')), json.dumps(c.comment)) for c in objs ]
        js_comments = '[%s]' % ','.join(l)

        js_text = 'res:{ rpt:%s,dist:%s,cat:%s,comm:%s,curr:%s }' % ( js_rpt, js_districts, js_cat, js_comments, js_currencies )

        return ajax_success('OK', js_text)
    except Exception as err:
        return HttpResponse(err.__str__(), status=500)

@login_required
@require_POST
@never_cache
def send_sms(request, report_id):

    if not request.POST.has_key('text'):
        return HttpResponse('Message not specified', status=400)
    
    if not request.POST.has_key('src'):
        return HttpResponse('Bad request. "src" missing', status=400)
    
    src = request.POST['src']
    if not re.search('^(report|log)$', src):
        return HttpResponse('Bad request. "src" not valid', status=400)

    if src == 'report':
        obj = get_object_or_404(IGReport, pk=report_id)
    else:
        obj = get_object_or_404(Message, direction='I', pk=report_id)

    text = request.POST['text'].strip()
    if not text or len(text) < 2:
        return HttpResponse('Message too short/not valid', status=400)

    try:
        dndlist = None
        qs = DNDList.objects.filter(msisdn=obj.connection.identity)
        if qs.count() > 0:
            return HttpResponse('Not Sent. %s is in DND List' % obj.connection.identity, status=400)
        
        sms.send_sms(dict(connection=obj.connection, text=text))
    except Exception as err:
        return HttpResponse(err.__str__(), status=500)

    return ajax_success()

@login_required
@require_POST
@never_cache
def demo_send(request):

    if not request.POST.has_key('text'):
        return HttpResponse('Message not specified', status=400)

    if not request.POST.has_key('sender'):
        return HttpResponse('Bad request. "sender" missing', status=400)

    text = request.POST['text'].strip()
    if not text or len(text) == 0:
        return HttpResponse('Message too short/not valid', status=400)

    try:
        params = dict(backend='youganda', dest='6009', message=text, sender=request.POST['sender'])
        system_url = getattr(settings, 'SYSTEM_URL', 'http://172.16.14.155:8081')
        url = '%s/router/receive/?%s' % (system_url, urllib.urlencode(params))
        
        res = urllib2.urlopen(urllib2.Request(url=url))
        response = res.read()
        #raise Exception(url)
    except Exception as err:
        return HttpResponse(err.__str__(), status=500)

    return ajax_success()

@login_required
@require_GET
@never_cache
def demo_get(request):

    if not request.GET.has_key('id'):
        return HttpResponse('ID not specified', status=400)

    if not request.GET.has_key('sender'):
        return HttpResponse('Bad request. "sender" missing', status=400)
    
    sender = request.GET['sender']
    
    if not re.search('^256[0-9]{9}$', sender):
        raise Exception('Bad sender')
    
    try:
        backend, created = Backend.objects.get_or_create(name='youganda', defaults={})
        connection, created = Connection.objects.get_or_create(
            identity = sender,
            backend = backend,
            defaults = {} 
        )
        cid = request.GET['id']
        msgs = Message.objects.filter(
            connection=connection, direction='O', id__gt=cid
        ).order_by('-date')[:1]
        
        if not msgs:
            return ajax_success('OK', 'res:{msg:null,id:%s}' % cid)
        
        msg = msgs[0]
        res = 'res:{msg:%s,id:%s}' % (json.dumps(msg.text), msg.id)
        return ajax_success('OK', res)
    
    except Exception as err:
        return HttpResponse(err.__str__(), status=500)

    return ajax_success()

@login_required
@require_POST
@csrf_exempt
def create_district(request):
    """
    Create new district
    """
    try:
        if not request.POST.has_key('name'):
            return ajax_error('District not specified')
        
        name = request.POST['name']
        qs = Location.objects.filter(type='district', name__iexact=name)
        if qs.count() > 0:
            return ajax_error('District already exists')
    
        tree_parent = Location.objects.get(type='country', name='Uganda')
        location_type = LocationType.objects.get(slug='district')
        district = Location(name=name.title(), type=location_type, tree_parent=tree_parent)
        
        district.save()
        log.info('User "%s" Added new district "%s"' % \
            (request.user.username, district.name))
        
    except Exception as err:
        return ajax_error(err.__str__())

    return HttpResponse( json.dumps(dict(error=False, msg='OK')) )

@login_required
@require_POST
@csrf_exempt
def edit_district(request, district_id):
    """
    Edit District
    """
    try:
        if not request.POST.has_key('name'):
            return ajax_error('District name not specified')
        
        name = request.POST['name']
        qs = Location.objects.filter(pk=district_id)
        
        if qs.count() == 0:
            return ajax_error('Invalid district identifier')
        
        district = qs[0]
        original_name = district.name
        
        count = IGReport.objects.filter(district=district).count()
        if count > 0:
            return ajax_error('You can not modify this district ' +
                'because it is associated with %s report(s)' % count)
        
        qs = Location.objects.filter(~Q(pk=district_id), type='district', name__iexact=name)
        
        if qs.count() > 0:
            return ajax_error('District already exists')

        district.name = name.title()
        district.save()
        
        log.info('User "%s" Changed district "%s" to "%s"' % \
            (request.user.username, original_name, district.name))
        
    except Exception as err:
        return ajax_error(err.__str__())

    return HttpResponse( json.dumps(dict(error=False, msg='OK')) )    