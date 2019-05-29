from high_frequency_trading.hft.exchange import OUCH
from twisted.internet.protocol import ClientFactory
from high_frequency_trading.hft.incoming_message import IncomingOuchMessage
from financial_market_simulator.utility import incoming_message_defaults
import logging

log = logging.getLogger(__name__)

class OUCHClient(OUCH):

    def __init__(self, trader):
        super()
        self.trader = trader

    def handle_incoming_data(self):
        original_msg = bytes(self.buffer)
        msg = IncomingOuchMessage(
            original_msg, **incoming_message_defaults)
        self.trader.handle_OUCH(msg)


class OUCHClientFactory(ClientFactory):

    protocol = OUCHClient

    def __init__(self, trader):
        super()
        self.trader = trader
        self.connection = None
    
    def buildProtocol(self, addr):
        log.debug('connecting to the exchange at %s' % addr)
        self.connection = self.protocol(self.trader)
        return self.connection