import configargparse
from twisted.internet import reactor
from protocols.ouch_proxy_protocol import ProxyOuchServerFactory, ProxyOuchClientFactory
from protocols.json_line_protocol import JSONLineServerFactory
from primitives.base_market_proxy import BaseMarketProxy
from proxies.elo_market_proxy import ELOMarketProxy
from utility import random_chars, stop_running_reactor
import settings
import logging as log


p = configargparse.getArgParser()
p.add('--session_duration', default=9999, type=int, 
    help='session duration in seconds')
p.add('--debug', action='store_true')
p.add('--session_code', default=random_chars(8))
p.add('--host', default='127.0.0.1')
p.add('--ouch_port', default=9201, type=int, help='port to listen to OUCH messages on')
p.add('--json_port', default=9202, type=int, help='port to listen to JSON messages on')
p.add('--exchange_host', default='127.0.0.1', help='Address of the matching engine to proxy')
p.add('--exchange_port', default=9001, type=int)
p.add('--tag', choices=['focal', 'external'], type=str)
options, args = p.parse_known_args()


def main(market_proxy_cls: BaseMarketProxy, settings: dict):    
    proxy_server = market_proxy_cls(
        options.tag, options.session_code, options.exchange_host, 
        options.exchange_port, **settings.simulation_parameters)

    reactor.connectTCP(options.exchange_host, options.exchange_port, 
                       ProxyOuchClientFactory(proxy_server))
    reactor.listenTCP(options.ouch_port, ProxyOuchServerFactory(proxy_server))
    reactor.listenTCP(options.json_port, JSONLineServerFactory(proxy_server))
    reactor.callLater(options.session_duration, stop_running_reactor, reactor)
    reactor.run()


if __name__ == '__main__':
    log.basicConfig(level= log.DEBUG if options.debug else log.INFO, 
        filename='logs/session_%s_market_%s.log' % (
        options.session_code, options.tag),
        format = "[%(asctime)s.%(msecs)03d] %(levelname)s \
            [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt = '%H:%M:%S')
    main(ELOMarketProxy, settings)


