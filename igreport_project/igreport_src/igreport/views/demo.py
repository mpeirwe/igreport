from django.template import RequestContext
from django.shortcuts import render_to_response
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

@require_GET
@never_cache
@login_required
def demo_view(request):
    
    template = 'igreport/demo.html'
    data = dict()
    
    return render_to_response(template, data, RequestContext(request))
    