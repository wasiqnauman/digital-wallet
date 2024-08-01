#!/usr/bin/env python
import socket, threading
from cprotocol import Cprotocol
from cmessage import Cmessage
import sqlite3 as sqldb
from serverops import *

DATABASE = "./data.db"


def logoutUser():
    m = Cmessage()
    m.setType('GOOD')
    m.addParam('Logout', 'Sucessful')
    cproto.putMessage(m)
    saveSession()
    return -1




def processMessage(cproto: Cprotocol, msg: Cmessage) -> int:
    type = msg.getType()
    print(f'[TPYE]:\t\t{type}')

    if type == 'LGIN':
        username = msg.getParam('username')
        password = msg.getParam('password')
        return loginUser(cproto, username, password)
    elif type == 'BLNC':
        return viewBalance(cproto, msg)
    elif type == "LOUT":
        return logoutUser()
    elif type == "RMSG":
        return getTransactions(cproto)
    elif type == 'CUSR':
        return createUser(cproto, msg)
    elif type == "LIST":
        return sendUserList(cproto)
    elif type == "SMNY":
        return sendMoneyToUser(cproto, msg)
    elif type == "TFND":
        return transferFunds(cproto, msg)
    elif type == "RQST":
        return requestFunds(cproto, msg)
    elif type == "RFND":
        return requestRefund(cproto, msg)
    else:
        print("Unknown message type")
        return 0

        
if __name__ == '__main__':
    # create the server socket
    #  defaults family=AF_INET, type=SOCK_STREAM, proto=0, filno=None
    serversoc = socket.socket()
    
    # bind to local host:5000
    serversoc.bind(("localhost",50000))
                   
    # make passive with backlog=5
    serversoc.listen(5)

    # wait for incoming connections
    while True:
        print("\nListening on ", 50000)
        
        # accept the connection
        commsoc, raddr = serversoc.accept()
        
        # run the application protocol
        cproto = Cprotocol(commsoc)
        
        AUTHENTICATED = False

        while True:
            msg = cproto.getMessage()
            print(f'\n[RECEIVED]:\t{msg}')
            r = processMessage(cproto, msg)
            if (r == 1):
                AUTHENTICATED = True
                print(f'[CURRENT USER]:\t{CURR_USER["username"]}')
            if (r == -1):
                print(f'{CURR_USER["username"]} disconnected from the server')
                CURR_USER.clear()
                
    
        # close the comm socket
        print("closing comm socket (Server)")
        cproto.close()
    
    # close the server socket
    serversoc.close()