import urllib2

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
        super(self, Request).__init__(*args, **kwargs)
        if content_type:
            self.add_unredirected_header('Content-type', content_type)

    def get_method(self):
        if self.method:
            return self.method.upper()
        return super(self, Request).get_method()

class Graph(object):
    FACEBOOK_GRAPH_URL = 'https://graph.facebook.com/'

    def __init__(self, facebook, path=None):
        self._facebook = facebook
        self._path = [path] if isinstance(path, basestring) else path or []

    def filter(self, path):
        return Graph(self._facebook, self._path + [path])

    def _request(self, method, data=None, content_type=None):
        if not self._path:
            raise AttributeError('No path given to graph object')
        url = self.FACEBOOK_GRAPH_URL + '/'.join(self._path)
        request = Request(url, data, method=method, content_type=content_type)
        if self._facebook.proxy:
            proxy_handler = urllib2.ProxyHandler(self._facebook.proxy)
            opener = urllib2.build_opener(proxy_handler)
            response = opener.open(request).read()
        else:
            response = urllib2.urlopen(request).read()
        return simplejson.loads(response)

    def get(self, **kwargs):
        self._request('GET', data=None, **kwargs)

    def post(self, data, content_type='application/json'):
        data = simplejson.dumps(data)
        self._request('POST', data, content_type=content_type)

    def delete(self, **kwargs):
        self._request('DELETE', data=None, **kwargs)

    def __iter__(self):
        return self.get()

    def __set__(self, val):
        return self.post(val)

