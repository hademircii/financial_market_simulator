import configargparse
from twisted.internet import reactor
from protocols.ouch_proxy_protocol import ProxyOuchServerFactory, ProxyOuchClientFactory
from protocols.json_line_protocol import JSONLineServerFactory
from proxies.elo_market_proxy import ELOMarketProxy
import logging as log
from utility import random_chars

p = configargparse.getArgParser()
p.add('--session_duration', required=True, type=int, 
    help='required: session duration in seconds')
p.add('--debug', action='store_true')
p.add('--session_id', default=random_chars(8))
p.add('--host', default='127.0.0.1')
p.add('--ouch_port', default=9201, help='port to listen to OUCH messages on')
p.add('--json_port', default=9202, help='port to listen to JSON messages on')
p.add('--exchange_host', default='127.0.0.1', help='Address of the matching engine to proxy')
p.add('--exchange_port', default=9001)
options, args = p.parse_known_args()


def main(market_proxy_cls):
    log.basicConfig(level= log.DEBUG if options.debug else log.INFO,
        format = "[%(asctime)s.%(msecs)03d] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt = '%H:%M:%S')
    
    proxy_server = market_proxy_cls(options.session_id, options.exchange_host, 
        options.exchange_port, session_duration=options.session_duration)

    reactor.connectTCP(options.exchange_host, options.exchange_port, 
        ProxyOuchClientFactory(proxy_server))
    reactor.listenTCP(options.ouch_port, ProxyOuchServerFactory(proxy_server))
    reactor.listenTCP(options.json_port, JSONLineServerFactory(proxy_server))
    reactor.callLater(options.session_duration, reactor.stop)
    reactor.run()

if __name__ == '__main__':
    main(ELOMarketProxy)


