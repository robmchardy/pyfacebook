import urllib
import urllib2
import urlparse

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
        query = urllib.urlencode({'access_token': self._facebook.oauth2_token})
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

if __name__ == '__main__':
    class Fakebook(object):
        oauth2_token = '2227470867|2.gQeACU_cgPMqzFjtXsUHHQ__.3600.1283281200-100001430902229|m3_rRaX8aqvP335DI79ib2eJyM0.'
        proxy = None
    g = Graph(Fakebook())
    print g.filter('btaylor').get()

