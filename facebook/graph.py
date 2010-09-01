import urllib
import urllib2
import urlparse

from django.http import HttpResponse, HttpResponseForbidden

try:
    import json as simplejson
    simplejson.loads
except (ImportError, AttributeError):
    try:
        import simplejson
        simplejson.loads
    except (ImportError, AttributeError):
        try:
            from django.utils import simplejson
            simplejson.loads
        except (ImportError, AttributeError):
            import jsonlib as simplejson
            simplejson.loads

class Request(urllib2.Request):
    def __init__(self, *args, **kwargs):
        self.method = kwargs.pop('method', None)
        content_type = kwargs.pop('content_type', None)
        urllib2.Request.__init__(self, *args, **kwargs)
        if content_type:
            self.add_unredirected_header('Content-type', content_type)

    def get_method(self):
        if self.method:
            return self.method.upper()
        return urllib2.Request.get_method(self)

class Graph(object):
    FACEBOOK_GRAPH_SCHEME = 'https'
    FACEBOOK_GRAPH_BASE = 'graph.facebook.com'

    def __init__(self, facebook, path=None):
        self._facebook = facebook
        self._path = [path] if isinstance(path, basestring) else path or []

    def filter(self, path):
        return Graph(self._facebook, self._path + [path])

    def _request(self, method, data=None, content_type=None):
        if not self._path:
            raise AttributeError('No path given to graph object')
        query = {}
        if getattr(self._facebook, 'oauth2_token', None):
            query['access_token'] = self._facebook.oauth2_token
        query = urllib.urlencode(query)
        url = urlparse.urlunparse((
            self.FACEBOOK_GRAPH_SCHEME,
            self.FACEBOOK_GRAPH_BASE,
            '/' + '/'.join(self._path),
            '',
            query,
            '',
        ))
        request = Request(url, data, method=method, content_type=content_type)
        if self._facebook.proxy:
            proxy_handler = urllib2.ProxyHandler(self._facebook.proxy)
            opener = urllib2.build_opener(proxy_handler)
            response = opener.open(request).read()
        else:
            response = urllib2.urlopen(request).read()
        if response:
            return simplejson.loads(response)
        return None

    def get(self, **kwargs):
        return self._request('GET', data=None, **kwargs)

    def post(self, data, content_type='application/json'):
        data = simplejson.dumps(data)
        return self._request('POST', data, content_type=content_type)

    def delete(self, **kwargs):
        return self._request('DELETE', data=None, **kwargs)

    def __iter__(self):
        return iter(self.get())

    def __set__(self, val):
        return self.post(val)

def subscription_callback(token):
    '''
    Use this to wrap views that are supposed to be used as real-time
    subscription callbacks.

    @subscription_callback('someUniqueToken')
    def someview(request, data):
        pass
    '''
    def inner_decorator(view):
        def wrapped(request, *args, **kwargs):
            if request.method == 'GET':
                hub_mode = request.GET.get('hub.mode', None)
                hub_challenge = request.GET.get('hub.challenge', None)
                hub_verify_token = request.GET.get('hub.verify_token', None)
                if hub_mode != 'subscribe' \
                        or not hub_challenge \
                        or hub_verify_token != token:
                    return HttpResponseForbidden('')
                return HttpResponse(hub_challenge)
            else:
                data = simplejson.loads(request.raw_post_data)
                return view(request, data, *args, **kwargs)
        wrapped.token = token
        return wrapped
    return inner_decorator

if __name__ == '__main__':
    class Fakebook(object):
        oauth2_token = '' # put a valid token here
        proxy = None
    g = Graph(Fakebook())
    print g.filter('btaylor').get()

