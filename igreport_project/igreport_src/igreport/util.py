# vim: ai ts=4 sts=4 et sw=4
# encoding=utf-8
import re
import xlrd
import string
import random
from django.utils.encoding import smart_str
from igreport import log

def error(message=None, code=None, log_error=False):
    if message is None:
        message = 'An error occured'
    if log_error:
        log.error(message)
    
    return dict(error=True, message=message, code=code)

def success(res=None):
    return dict(error= False, result= res)

"""
Get a unique reference number. The generated reference 
number should start in the primary key value.

@param int pk   The primary key IGReport.id
                whose max value is 2147483647
                
@return str returns the reference number
"""
def get_reference_number(pk):
    
    sep = '0'
    maxval = 2147483647
    
    if pk >= maxval:
        return '%s%s' % (pk, sep)
    
    maxlen = len('%s' % maxval)
    pklen = len( '%s' % pk ) 
    digits = maxlen - pklen
    
    rand = generate_random_str(digits, string.digits)
    reference_number = '%s%s%s' % (pk, sep, rand)
    
    return reference_number
    
def generate_random_str(size=6, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

def get_tagline(connection):
    if not connection.identity:
        return ''
    
    if re.search('^256(77|78)', connection.identity):
        return '\n\nSupported by MTN'
    
    return ''

def truncate_str(value, limit):
	if not value:
		return smart_str(value)
	if len(value) > limit:
		value = (value[0:limit]) + '..'
	return value

def import_contacts_from_xls_file(request, form):
    """
    Extract a list of phone number from an Excel sheet
    
    @param object request           HTTP request var
    @param object form              HTTP form var
    """
    try:
        msisdns = list()
        if not request.FILES.has_key('recipients_file'):
            return success()

        file = request.FILES['recipients_file']
        path = file.temporary_file_path()
        index = 0 # sheet number

        book = xlrd.open_workbook(filename=path, logfile='/tmp/xls.log')
        sheet = book.sheet_by_index(index)

        for i in range(1, sheet.nrows):
            row = sheet.row(i)
            number = smart_str(row[0].value)
            number = number.lstrip()

            if not number:
                # XXXX not a valid number
                continue
            msisdns.append(number)

        if not msisdns:
            return error('No valid phone number was found in the uploaded file')

        return success(msisdns)

    except Exception as err:
        log.exception()
        return error( err.__str__() )

def import_recipients_from_xls_file(request, form):
    return import_contacts_from_xls_file(request, form)