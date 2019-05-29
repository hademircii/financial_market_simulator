from twisted.internet import protocol, reactor
from twisted.protocols import basic
import json
import random
import logging

log = logging.getLogger(__name__)

# well this is a quick solution to send
# json over network, obviously newline 
# character \n is not allowed in these messages

# I should revisit this once we write a protocol
# for public messages

class JSONLineServerProtocol(basic.LineReceiver):

    def __init__(self, market, users):
        self.market = market
        self.users = users
        self.account_id = None
        self.state = 'GETACCOUNTID'

    def connectionMade(self):
        self.sendLine('send account id..')

    def connectionLost(self):
        if self.account_id in self.users:
            log.debug('user %s disconnected' % self.account_id)
            del self.users[self.account_id]
    
    def lineReceived(self, line):
        try:
            dict_msg = json.loads(line)
        except:
            log.exception('failed to convert line to json, ignoring: %s' % line)
        else:
            if self.state == 'GETACCOUNTID': 
                if 'account_id' in dict_msg:
                    if account_id not in self.users:
                        self.users[account_id] = self
                        self.account_id = dict_msg['account_id']
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
        self.users = {}
    
    def buildProtocol(self, addr):
        return self.protocol(self.users, self.market)
    
    def broadcast(self, msg, shuffle=True):
        if not isinstance(msg, str):
            try:
                json_msg = json.dumps(msg)
            except:
                log.exception('failed to convert json: %s' % json_msg)
        else:
            json_msg = msg
        if '\n' in json_msg:
            raise Exception('new line character is not allowed: %s' % json_msg)
        connections = [conn for conn in self.users.values()]
        if connections:
            if shuffle:
                random.shuffle(connections)
            for c in connections:
                c.sendLine(json_msg)



class JSONLineClientProtocol(basic.LineReceiver):
    
    def __init__(self, type_code, trader):
        self.type_code = type_code
        self.trader = trader
    
    def connectionMade(self):
        self.sendLine(
            json.dumps({'type': 'greet', 'account_id': self.trader.account_id})
            )
        
    def lineReceived(self, line):
        try:
            dict_msg = json.loads(line)
        except:
            log.exception('failed to convert line to json, ignoring: %s' % line)
        self.trader.handle_JSON(dict_msg, self.type_code)


class JSONLineClientFactory(protocol.ClientFactory):
    protocol = JSONLineClientProtocol

    def __init__(self, type_code, trader):
        self.type_code = type_code
        self.trader = trader
    
    def buildProtocol(self, addr):
        log.debug('connected to %s' % addr)
        return self.protocol(self.type_code, self.trader)


