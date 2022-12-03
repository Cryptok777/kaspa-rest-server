import sockets

from endpoints.stats import *
from endpoints.address import *
from endpoints.block import *
from endpoints.transcation import *

from endpoints.dashboard import *

from sockets.blockdag import periodical_blockdag
from sockets.bluescore import periodical_blue_score
from sockets.coinsupply import periodic_coin_supply
