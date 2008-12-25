 
def redirect(start_response, location, permanent=None):
    header=[('location',location),
                 ('Content-Type',"text/plain")]
    if permanent:
        start_response('301 Moved Permanently', header)
    else:
        start_response('302 Moved Temporarily', header)
    return []

