#
# (c) 2017 elias/vanissoft
#
#


PORT = 8801
REDIS_PORT = 6385
#QSERVER = "http://23.94.69.140:5000"
#WSS_NODE = "wss://node.testnet.bitshares.eu"
#HTTP_NODE = "https://node.testnet.bitshares.eu"
WSS_NODE = "wss://bitshares.openledger.info/ws"
HTTP_NODE = "http://209.188.21.157:8090/rpc"
PREFIX = "BTS"

import redis

Redisdb = redis.StrictRedis(host='127.0.0.1', port=REDIS_PORT, db=1)

from bitshares import BitShares
Bitshares = BitShares(WSS_NODE)
