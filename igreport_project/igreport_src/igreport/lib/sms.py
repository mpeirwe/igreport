from igreport.models import DNDList
from rapidsms.models import Connection
from rapidsms_httprouter.models import Message

"""
Queue an Outgoing SMS
@param dict params      A dict with the following keys:
                        application => The application (optional)
                        connection => Connection object
                        text => The message text
                        
@param list dndlist     A list of "Do Not Disturb" phone numbers                        
"""
def send_sms(params, dndlist=None):
    try:
        if not dndlist:
            objs = DNDList.objects.all()
            if objs.count() > 0:
                dndlist = [ obj.msisdn for obj in objs ]
                
        if not dndlist:
            dndlist = list()
            
        if dndlist:
            if dndlist.__contains__(params['connection'].identity):
                print '%s in DND List. Not sent ..' % params['connection'].identity
                return
            
        args = dict(direction='O', status='Q', connection=params['connection'], text=params['text'])
        if params.has_key('application'):
            args['application'] = params['application']
            
        Message.objects.create(**args)
    except Exception as err:
        pass