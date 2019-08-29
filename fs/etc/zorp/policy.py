
from Zorp.Core *
from Zorp.Http import *

config.options.kzorp_enabled = False


class HealthzHttpProxy(HttpProxy):
        def config(self):
                HttpProxy.config(self)
                self.error_silent = TRUE
                self.request["GET"] = (HTTP_REQ_POLICY,self.reqRedirect)

        def reqRedirect(self, method, url, version):
                self.error_status = 200
                self.error_msg = OK
                self.error_info = 'HTTP/1.0 200 OK'
                return HTTP_REQ_REJECT

def default():
    Service(name='healthz', router=DirectedRouter(dest_addr=(SockAddrInet('127.0.0.1', 4000)), overrideable=TRUE), chainer=ConnectChainer(), proxy_class=HealthzHttpProxy, max_instances=0, max_sessions=0, keepalive=Z_KEEPALIVE_NONE)
    Dispatcher(transparent=FALSE, bindto=DBIface(protocol=ZD_PROTO_TCP, port=1042, iface="eth0", family=2), rule_port="1042", service="healthz")

