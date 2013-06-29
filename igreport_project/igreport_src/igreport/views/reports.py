#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
# encoding=utf-8

import re
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

from django.template import RequestContext
from igreport.models import IGReport, Report, Category, Currency
from igreport.models import UserProfile
from igreport import util
from igreport.lib import reports

from rapidsms.contrib.locations.models import Location
from datetime import datetime

@require_GET
@login_required
@never_cache
def show_reports(request, **kwargs):
    report_filter = request.GET.get('filter', 'all')
    print report_filter
    reports = IGReport.objects.all()

    if not request.user.is_staff:
        try:
            reports = reports.filter(district=request.user.get_profile().district)
        except UserProfile.DoesNotExist:
            return HttpResponse('', status=404)

    if report_filter == 'incomplete':
        reports = reports.filter(completed=False)
    elif report_filter == 'completed':
        reports = reports.filter(completed=True, synced=False)
    elif report_filter == 'synced':
        reports = reports.filter(synced=True)


    reports = reports.order_by('synced', 'completed', '-datetime')

    return render_to_response("igreport/igreports.html", {\
        'reports':reports
    }, context_instance=RequestContext(request))


@require_POST
@login_required
def submit_report(request, report_id):
    
    try:
        report = get_object_or_404(IGReport, pk=long(report_id))
        
        if report.synced:
            raise Exception('This report has already been synced. No changes can be made to it')
        
        if report.closed:
            raise Exception('This report was closed. No changes can be made to it')
        
        report.categories.clear()
        
        if 'category' in request.POST and request.POST['category']:
            for category in request.POST.getlist('category'):
                try:
                    report.categories.add(Category.objects.get(id=long(category)))
                except Category.DoesNotExist:
                    return HttpResponse('Invalid category ID', status=400)
                
        if 'district' in request.POST and request.POST['district']:
            try:
                report.district = Location.objects.get(id=long(request.POST['district']))
            except Location.DoesNotExist:
                return HttpResponse('Invalid District ID', status=400)
            
        if 'currency' in request.POST and request.POST['currency']:
            try:
                report.currency = Currency.objects.get(id=request.POST['currency'])
            except Location.DoesNotExist:
                return HttpResponse('Invalid Currency ID', status=400)            
            
        if 'comments' in request.POST:
            for comment in request.POST.getlist('comments'):
                if comment:
                    report.comments.create(user=request.user, comment=comment)

        report.subject = request.POST['subject'] if 'subject' in request.POST else ''
        report.report = request.POST['report'] if 'report' in request.POST else ''
        report.names = request.POST['names'] if 'names' in request.POST else ''
        
        if 'amount' in request.POST and request.POST['amount']:
            try:
                amount = re.sub(',', '', request.POST['amount'])
                report.amount = float(amount)
            except ValueError:
                return HttpResponse('Invalid Amount', status=400)
        
        if request.POST.has_key('closed'):
            report.closed = True
            
        report.save()
        
    except Exception as err:
        return HttpResponse(err.__str__(), status=500)
    
    return HttpResponse('OK', status=200)

@require_GET
@login_required
def accept_report(request, report_id):
    error = reports.accept_report(report_id)
    if error:
        return HttpResponse(error, status=400)
    
    return HttpResponseRedirect('/admin/igreport/igreport/')    