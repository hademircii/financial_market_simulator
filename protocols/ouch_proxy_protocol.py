from twisted.internet import protocol, reactor
from high_frequency_trading.hft.incoming_message import IncomingOuchMessage
from utility import incoming_message_defaults
from high_frequency_trading.hft.exchange import OUCH
import random
import logging

log = logging.getLogger(__name__)


class ProxyOuchServerProtocol(OUCH):
    name = 'private OUCH channel'

    def __init__(self, market, users):
        super().__init__()
        self.market = market 
        self.users = users
        self.account_id = None
        self.state = 'GETACCOUNTID'

    def handle_incoming_data(self, header):
        original_msg = bytes(self.buffer)
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
                    log.info('registered account id %s to %s.' % (account_id, 
                        self.name))
                else:
                    log.error('account id is already taken..ignoring message %s' % msg)
        else:
            self.market.handle_OUCH(msg, original_msg, 2)


class ProxyOuchServerFactory(protocol.ServerFactory): 
    protocol = ProxyOuchServerProtocol

    def __init__(self, market):
        super()
        self.market = market
        market.ouch_server_factory = self
        self.users = {}

    def buildProtocol(self, addr):
        conn = self.protocol(self.market, self.users)
        self.market.ouch_server_factory = self
        return conn

    def broadcast(self, msg, shuffle=True):
        connections = [conn for conn in self.users.values()]
        if connections:
            if shuffle:
                random.shuffle(connections)
            for c in connections:
                c.sendMessage(msg, 0)

class ProxyOuchClient(OUCH):

    def __init__(self, market):
        super().__init__()
        self.market = market 

    def handle_incoming_data(self, header):
        original_msg = bytes(self.buffer)
        msg = IncomingOuchMessage(
            original_msg, **incoming_message_defaults)
        self.market.handle_OUCH(msg, original_msg, 1)     

    def connectionMade(self):
        log.info('connected to exchange')


class ProxyOuchClientFactory(protocol.ClientFactory):

    protocol = ProxyOuchClient  

    def __init__(self, market):
        super()
        self.market = market

    def buildProtocol(self, addr):
        conn = self.protocol(self.market)
        self.market.exchange_connection = conn
        return conn
