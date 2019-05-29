from twisted.internet import protocol, reactor
from high_frequency_trading.hft.incoming_message import IncomingOuchMessage
from financial_market_simulator.utility import incoming_message_defaults
from high_frequency_trading.hft.exchange import OUCH
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class ProxyOuchServer(OUCH):

    def __init__(self, market, users):
        self.market = market 
        self.users = users
        self.account_id = None
        self.state = 'GETACCOUNTID'

    def handle_incoming_data(self, header):
        original_msg = self.buffer
        msg = IncomingOuchMessage(
            original_msg, **incoming_message_defaults)
        if self.state == 'GETACCOUNTID':
            try:
                account_id = msg.firm
            except AttributeError:
                log.error('account id is not set..ignoring message %s' % msg)
            else:
                if account_id not in self.users:
                    self.users[account_id] = self
                    self.state = 'TRADE'
                else:
                    log.error('account id is already taken..ignoring message %s' % msg)
        else:
            self.market.handle_OUCH(msg, original_msg)


class ProxyOuchServerFactory(protocol.ServerFactory): 
    protocol = ProxyOuchServer

    def __init__(self, market):
        super()
        self.market = market
        self.users = {}

    def buildProtocol(self, addr):
        return self.protocol(self.market, self.users)


class ProxyOuchClient(OUCH):

    def __init__(self, market):
        self.market = market 

    def handle_incoming_data(self, header):
        original_msg = self.buffer
        msg = IncomingOuchMessage(
            original_msg, **incoming_message_defaults)
        self.market.handle_OUCH(msg, original_msg, 1)     

    def connectionMade(self):
        log.debug('connected to exchange')


class ProxyOuchClientFactory(protocol.ClientFactory):

    protocol = ProxyOuchClient  

    def __init__(self, market):
        super()
        self.market = market

    def buildProtocol(self, addr):
        return self.protocol(self.market)
