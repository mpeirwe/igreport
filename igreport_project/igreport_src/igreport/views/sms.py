from django.http import HttpResponse

def drop_message(request):
    return HttpResponse('OK', status=200)