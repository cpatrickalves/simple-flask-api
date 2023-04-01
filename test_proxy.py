from urllib3 import PoolManager, HTTPConnectionPool, HTTPSConnectionPool
from urllib3.connection import HTTPConnection, HTTPSConnection
from python_socks.sync import Proxy


class ProxyHTTPConnection(HTTPConnection):
    def __init__(self, *args, **kwargs):
        socks_options = kwargs.pop('_socks_options')
        self._proxy_url = socks_options['proxy_url']
        super().__init__(*args, **kwargs)

    def _new_conn(self):
        proxy = Proxy.from_url(self._proxy_url)
        return proxy.connect(
            dest_host=self.host,
            dest_port=self.port,
            timeout=self.timeout
        )


class ProxyHTTPSConnection(ProxyHTTPConnection, HTTPSConnection):
    pass


class ProxyHTTPConnectionPool(HTTPConnectionPool):
    ConnectionCls = ProxyHTTPConnection


class ProxyHTTPSConnectionPool(HTTPSConnectionPool):
    ConnectionCls = ProxyHTTPSConnection


class ProxyPoolManager(PoolManager):
    def __init__(self, proxy_url, timeout=5, num_pools=10, headers=None,
                 **connection_pool_kw):

        connection_pool_kw['_socks_options'] = {'proxy_url': proxy_url}
        connection_pool_kw['timeout'] = timeout

        super().__init__(num_pools, headers, **connection_pool_kw)

        self.pool_classes_by_scheme = {
            'http': ProxyHTTPConnectionPool,
            'https': ProxyHTTPSConnectionPool,
        }


### and how to use it
manager = ProxyPoolManager('socks5://127.0.0.0.1:43837')
response = manager.request('GET', 'https://check-host.net/ip')
print(response.data)
