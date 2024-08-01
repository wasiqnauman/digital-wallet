#!/usr/bin/env python
import socket
from cprotocol import Cprotocol
from cmessage import Cmessage
from clientops import *



if __name__ == '__main__':
    # create the socket
    #  defaults family=AF_INET, type=SOCK_STREAM, proto=0, filno=None
    commsoc = socket.socket()
    
    # connect to localhost:5000
    commsoc.connect(("localhost",50000))
    
    # run the application protocol
    cproto = Cprotocol(commsoc)
    r = 1
    while r == 1:
        r = menu(cproto)
        if r == -1:
            break
    # close the comm socket
    print("closing comm socket")
    cproto.close()
    exit()