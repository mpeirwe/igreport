import re
import json
import urllib, urllib2
from django.utils import simplejson
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from rapidsms.contrib.locations.models import Location, LocationType
from rapidsms_httprouter.models import Message
from rapidsms.models import Connection, Backend
from django.conf import settings
from igreport.models import IGReport, Currency, Category, Comment

def ajax_success(msg=None, js_=None):
    if msg is None:
        msg = 'OK'

    if js_ is None:
        js = '{error:false, msg:"%s"}' % msg
    else:
        js = '{error:false, msg:"%s", %s}' % (msg, js_)
    return HttpResponse(js, mimetype='text/plain', status=200)

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
        Message.objects.create(direction='O', status='Q', connection=obj.connection, text=text)
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
        #raise Exception(response)
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
        
        msgs = Message.objects.filter(connection=connection, direction='O', status='P').order_by('-date')[:1]
        if not msgs:
            return ajax_success('OK', 'ret:{msg:null,id:0}')
        
        msg = msgs[0]
        if request.GET['id'] == str(msg.id):
            return ajax_success('OK', 'ret:{msg:null,id:0}')
        
        res = 'res:{msg:%s,id:%s}' % (json.dumps(msg.text), msg.id)
        return ajax_success('OK', res)
    
    except Exception as err:
        return HttpResponse(err.__str__(), status=500)

    return ajax_success()