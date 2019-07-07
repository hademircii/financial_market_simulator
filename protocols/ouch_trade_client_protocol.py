from high_frequency_trading.hft.exchange import OUCH
from twisted.internet.protocol import ClientFactory
from high_frequency_trading.hft.incoming_message import IncomingOuchMessage
from utility import incoming_message_defaults
import logging

log = logging.getLogger(__name__)

class OUCHClientProtocol(OUCH):

    def __init__(self, trader):
        super().__init__()
        self.trader = trader

    def connectionMade(self):
        super()
        self.trader.exchange_connection = self

    def handle_incoming_data(self, header):
        original_msg = bytes(self.buffer)
        msg = IncomingOuchMessage(
            original_msg, **incoming_message_defaults)
        self.trader.handle_OUCH(msg)


class OUCHClientFactory(ClientFactory):

    protocol = OUCHClientProtocol

    def __init__(self, trader):
        super()
        self.trader = trader
    
    def buildProtocol(self, addr):
        log.info('connecting to the exchange at %s' % addr)
        conn = self.protocol(self.trader)
        return conn
