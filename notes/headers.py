

# ACCESSING HEADER DATA

def main (request):
    
    attr = request.session['HX-PROMPT'] = request.headers['HX-PROMPT']
    
    return attr

