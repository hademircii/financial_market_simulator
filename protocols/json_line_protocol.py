from twisted.internet import protocol, reactor
from twisted.protocols import basic
from high_frequency_trading.hft.outbound_message_primitives import OutboundMessage
import json
import random
import logging

log = logging.getLogger(__name__)

# well this is a quick solution to send
# json over network, a line oriented protocol
# obviously newline character \n is not allowed
#  in these messages

# I should revisit this after I write a protocol
# for public messages

class JSONLineServerProtocol(basic.LineReceiver):
    name = 'public JSON channel'

    def __init__(self, market, users):
        self.market = market
        self.users = users
        self.account_id = None
        self.state = 'GETACCOUNTID'

    def connectionLost(self, reason):
        if self.account_id in self.users:
            log.info('user %s disconnected' % self.account_id)
            del self.users[self.account_id]
    
    def lineReceived(self, line):
        str_line = line
        if isinstance(line, bytes):
            str_line = line.decode('utf-8')
        try:
            dict_msg = json.loads(str_line)
        except:
            log.exception('failed to convert line to json, ignoring: %s' % line)
        else:
            if self.state == 'GETACCOUNTID': 
                if 'account_id' in dict_msg:
                    account_id = dict_msg['account_id']
                    if account_id not in self.users:
                        self.account_id = account_id
                        self.users[account_id] = self
                        log.info('account %s registered to %s.' % (account_id, 
                            self.name))
                    else:
                        log.error('Account id %s is already taken..' % account_id)
                        return 
                    self.state = 'TRADE'
                else:
                    log.error('account id is not set..ignoring message %s' % dict_msg)
            else:
                self.market.handle_JSON(dict_msg, account_id)


class JSONLineServerFactory(protocol.ServerFactory):

    protocol = JSONLineServerProtocol

    def __init__(self, market):
        super()
        self.market = market
        market.json_server_factory = self
        self.users = {}
    
    def buildProtocol(self, addr):
        return self.protocol(self.market, self.users)
    
    def broadcast(self, msg: OutboundMessage, shuffle=True):
        if isinstance(msg, OutboundMessage):
            try:
                json_msg = msg.to_json()
            except:
                log.exception('failed to convert json: %s' % json_msg)
        else:
            raise TypeError('invalid msg type %s' % msg.__class__)
        if '\n' in json_msg:
            raise ValueError('new line character is not allowed: %s' % json_msg)
        connections = [conn for conn in self.users.values()]
        bytes_json_msg = bytes(json_msg, 'utf-8')
        log.info('broadcasting to: %s --> %s ' % (':'.join(c.account_id 
                  for c in connections), msg))
        if connections:
            if shuffle:
                random.shuffle(connections)
            for c in connections:
                c.sendLine(bytes_json_msg)



class JSONLineClientProtocol(basic.LineReceiver):
    
    def __init__(self, type_code, trader):
        self.type_code = type_code
        self.trader = trader
    
    def connectionMade(self):
        msg = json.dumps({'type': 'greet', 'account_id': self.trader.account_id})
        log.info('registering with account id %s' % self.trader.account_id)
        self.sendLine(bytes(msg, 'utf-8'))
        
    def lineReceived(self, line):
        str_line = line
        if isinstance(line, bytes):
            str_line = line.decode('utf-8')
        try:
            dict_msg = json.loads(str_line)
        except:
            log.warning('failed to convert line to json, ignoring: %s' % line)
        else:
            self.trader.handle_JSON(dict_msg, self.type_code)


class JSONLineClientFactory(protocol.ClientFactory):
    protocol = JSONLineClientProtocol

    def __init__(self, type_code, trader):
        self.type_code = type_code
        self.trader = trader
    
    def buildProtocol(self, addr):
        log.info('connected to %s' % addr)
        return self.protocol(self.type_code, self.trader)

    def clientConnectionLost(self, connector, reason):
        log.info('reconnecting..')
        connector.connect()



