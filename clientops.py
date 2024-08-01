#!/usr/bin/env python
import socket, threading
from cprotocol import Cprotocol
from cmessage import Cmessage
import sqlite3 as sqldb
from time import sleep
# from serverops import *


DATABASE = "./data.db"

CURR_USER = {}

def displayAccountBalance(response):
    user = response.getParam('user')
    balance = response.getParam('balance')
    print('\n----------------------------------------------------------------')
    print('\nACCOUNT BALANCE REMAINING')
    print('\n----------------------------------------------------------------')
    print('\nUser\t\tBalance')
    print(f'\n{user}\t\t{balance}')
    print('\n----------------------------------------------------------------')

def displayTransactions(transactions):
    print('\n----------------------------------------------------------------')
    print('\nACCOUNT TRANSACTIONS LIST')
    print('\n----------------------------------------------------------------')
    print('ID\tTO\tFROM\tTYPE\tSTATUS\tAMOUNT\tCREATED\tCOMPLETED')
    print('----------------------------------------------------------------')
    print(type(transactions))


def getUserBalance(cproto: Cprotocol):
    m = Cmessage()
    m.setType('BLNC')
    cproto.putMessage(m)
    response = cproto.getMessage()
    if response.getType() != 'ERR':
        displayAccountBalance(response)
    else:
        print('\nUnable to get account balance')

def viewAllTransactions(cproto: Cprotocol):
    print('\n---------------------------------------------------------------------------------------')
    print('ID\tTO\tFROM\tTYPE\tSTATUS\t\tAMOUNT\tCREATED\t\t\tCOMPLETED')
    print('---------------------------------------------------------------------------------------')
    m = Cmessage()
    m.setType('RMSG')
    cproto.putMessage(m)
    listSize = int(cproto.getMessage().getParam('listSize'))
    transactions = []
    for i in range(listSize):
        m = cproto.getMessage()
        ID = m.getParam('id')
        TO = m.getParam('to')
        FROM = m.getParam('from')
        TYPE = m.getParam('type')
        STATUS = m.getParam('status')
        AMOUNT = m.getParam('amount')
        CREATED = m.getParam('created')
        COMPLETED = m.getParam('completed')
        if TO == CURR_USER["username"] and STATUS == 'CANCELLED':
            continue
        print(f'\n{ID}\t{TO}\t{FROM}\t{TYPE}\t{STATUS}\t{AMOUNT}\t{CREATED}\t{COMPLETED}')
        

def getPendingTransactions(cproto: Cprotocol):
    print('\n--------------------------------------------------------------------')
    print('ID\tTO\tFROM\tTYPE\tSTATUS\tAMOUNT\tCREATED\t\t\tCOMPLETED')
    print('----------------------------------------------------------------------')
    m = Cmessage()
    m.setType('RMSG')
    cproto.putMessage(m)
    listSize = int(cproto.getMessage().getParam('listSize'))
    transactions = []
    for i in range(listSize):
        m = cproto.getMessage()
        t = {}
        t["ID"] = m.getParam('id')
        t["TO"] = m.getParam('to')
        t["FROM"] = m.getParam('from')
        t["TYPE"] = m.getParam('type')
        t["STATUS"] = m.getParam('status')
        t["AMOUNT"] = m.getParam('amount')
        t["CREATED"] = m.getParam('created')
        t["COMPLETED"] = m.getParam('completed')
        
        # only get pending transactions
        if t["STATUS"] != 'PENDING':
            continue
        
        transactions.append(t)
        print(f'\n{t["ID"]}\t{t["TO"]}\t{t["FROM"]}\t{t["TYPE"]}\t{t["STATUS"]}\t{t["AMOUNT"]}\t{t["CREATED"]}\t{t["COMPLETED"]}')
        # condition 1 and 2 ---------                                                                         condition 3
        if (t['TO'] == CURR_USER["username"] and t['TYPE'] == 'SEND') or (t['TO'] == CURR_USER["username"] and t['TYPE'] == 'REQUEST') or (t['TO'] == CURR_USER["username"] and t['TYPE'] == 'REFUND'):
            print('1. Accept')
            print('2. Decline')
            print('3. View Next')
            userChoice = int(input('>'))
            if userChoice == 1:
                handleTransaction(cproto, t, 'ACCEPTED', t["TYPE"])
            elif userChoice == 2:
                handleTransaction(cproto, t, 'DECLINED', t["TYPE"])
            else:
                continue
        else:
            print('1. Cancel')
            print('2. View Next')
            userChoice = int(input('>'))
            if userChoice == 1:
                handleTransaction(cproto, t, 'CANCELLED', t["TYPE"])
            else:
                continue
        # else:
        #     continue
        
    print('End of transactions')



def requestRefund(cproto):
    print('\n--------------------------------------------------------------------')
    print('ID\tTO\tFROM\tTYPE\tSTATUS\tAMOUNT\tCREATED\t\t\tCOMPLETED')
    print('----------------------------------------------------------------------')
    m = Cmessage()
    m.setType('RMSG')
    cproto.putMessage(m)
    listSize = int(cproto.getMessage().getParam('listSize'))
    transactions = []
    for i in range(listSize):
        m = cproto.getMessage()
        t = {}
        t["ID"] = m.getParam('id')
        t["TO"] = m.getParam('to')
        t["FROM"] = m.getParam('from')
        t["TYPE"] = m.getParam('type')
        t["STATUS"] = m.getParam('status')
        t["AMOUNT"] = m.getParam('amount')
        t["CREATED"] = m.getParam('created')
        t["COMPLETED"] = m.getParam('completed')
        
        # only get COMPLETED transactions
        if t["STATUS"] != 'COMPLETED':
            continue
        # cant refund a completed refund transaction
        if t['TYPE'] == 'REFUND':
            continue
        transactions.append(t)
        
        if (t['FROM'] == CURR_USER["username"] and t['TYPE'] != 'REQUEST') or (t['TYPE'] == 'REQUEST' and t['TO'] == CURR_USER["username"]):
            print(f'\n{t["ID"]}\t{t["TO"]}\t{t["FROM"]}\t{t["TYPE"]}\t{t["STATUS"]}\t{t["AMOUNT"]}\t{t["CREATED"]}\t{t["COMPLETED"]}')
            print('1. Request a refund')
            print('2. View Next')
            userChoice = int(input('>'))
            if userChoice == 1:
                m = Cmessage()
                m.setType('RFND')
                m.addParam('amount', t["AMOUNT"])
                m.addParam('tID', t["ID"])
                m.addParam('to', t["FROM"])     # to and from will be swapped as the refund will reverse the transaction
                m.addParam('from', t["TO"])
                m.addParam('message', 'refund')
                m.addParam('flag', 'REFUNDED')
                m.addParam('ttype', 'REFUND')
                cproto.putMessage(m)
            else:
                continue
        
    print('End of transactions')

def transferFunds(cproto, recipient, author, amount, transactionID, flag, ttype):
    m = Cmessage()
    m.setType('TFND')
    m.addParam('to', recipient)
    m.addParam('from', author)
    m.addParam('amount', amount)
    m.addParam('tID', transactionID)
    m.addParam('flag', flag)
    m.addParam('ttype', ttype)
    cproto.putMessage(m)

def handleTransaction(cproto, t, flag, ttype):
    transferFunds(cproto, t["TO"], t["FROM"], t["AMOUNT"], t["ID"], flag, ttype)


def getUserAccList(cproto: Cprotocol):

    m = Cmessage()
    m.setType('LIST')
    cproto.putMessage(m)
    listSize = int(cproto.getMessage().getParam('listSize'))
    accList = {}
    for acc in range(listSize):
        m = cproto.getMessage()
        id = m.getParam('id')
        username = m.getParam('username')
        accList[id] = username
    
    return accList

def requestMoney(cproto: Cprotocol, ttype):
    accList = getUserAccList(cproto)
    print('--------------------------------------------------------------------')
    print('SEND MONEY')
    print('--------------------------------------------------------------------')
    print('\nID\t\tUSERNAME')
    for id, username in accList.items():
        if username != CURR_USER["username"] and id != CURR_USER["ID"]:
            print(f'{id}\t\t{username}')
    print('Select user to request money from')
    userChoice = int(input('ID:'))
    amount = int(input('Amount: '))
    message = str(input('Message:'))
    m = Cmessage()
    m.setType('RQST')
    m.addParam('amount', amount)
    m.addParam('to', userChoice)
    m.addParam('message', message)
    m.addParam('ttype', ttype)
    cproto.putMessage(m)

def sendMoney(cproto: Cprotocol):
    accList = getUserAccList(cproto)
    print('--------------------------------------------------------------------')
    print('SEND MONEY')
    print('--------------------------------------------------------------------')
    print('\nID\t\tUSERNAME')
    for id, username in accList.items():
        if username != CURR_USER["username"] and id != CURR_USER["ID"]:
            print(f'{id}\t\t{username}')
    print('Select user to send money to')
    userChoice = int(input('ID:'))
    amount = int(input('Amount: '))
    message = str(input('Message:'))
    m = Cmessage()
    m.setType('SMNY')
    m.addParam('amount', amount)
    m.addParam('to', userChoice)
    m.addParam('message', message)
    cproto.putMessage(m)

def addFundsToWallet(cproto):
    print('Please enter credit card details')
    name = input('Name:')
    CC = int(input('CC #: '))
    EXP = int(input('EXP(mmyy): '))
    CVV = int(input('CVV:'))
    amount = int(input('Amount: '))
    print('Contacting bank API', end='')
    for i in range(3):
        print('.', end='', flush='True')
        sleep(0.5)
    print('\nVerifying Card information', end='')
    for i in range(10):
        print('.', end='', flush='True')
        sleep(0.5)
    print('\nUnable to verify credit card information')

def viewOfflineBalance():
    print('ID\t\tName\t\tBalance')
    with open('userInfo.txt') as f:
        data = f.readline().split(' ')
        print(f'{data[0]}\t\t{data[1]}\t\t{data[2]}\t\t')



def createUser(cproto):
    username = input("username:")
    password = input("password:")
    m = Cmessage()
    m.setType('CUSR')
    m.addParam('username', username)
    m.addParam('password', password)
    cproto.putMessage(m)
    m = cproto.getMessage()
    if m.getType() == 'GOOD':
        print('Account created successfully')

def menu(cproto: Cprotocol):
    loggedIn = False
    while not loggedIn:
        print("\nWelcome to the Digital Wallet app")
        print("Please make a selection from the list below:")
        print("1. Login")
        print("2. View Balance")
        print("3. Signup")
        print("4. Exit")
        choice = int(input('>'))
        if choice == 1:
            loggedIn = loginClient(cproto)
            if loggedIn:
                loginMenu(cproto)
        elif choice == 2:
            viewOfflineBalance()
        elif choice == 3:
            createUser(cproto)
        elif choice == 4:
            print("Exiting")
            return -1
            
        else:
            return 0
            
    
def logoutUser(cproto: Cprotocol):
    m = Cmessage()
    m.setType('LOUT')
    cproto.putMessage(m)
    print(f'\n[SENT]:\t\t{m}')
    m6 = cproto.getMessage()
    print(f'[RECIEVED]:\t{m6}')
    menu(cproto)

def loginMenu(cproto: Cprotocol):
    loggedIn = True
    while loggedIn:
        print('--------------------------------------------------------------------')
        print('LOGGED IN MENU')
        print('--------------------------------------------------------------------')
        print("Please make a selection from the list below:")
        print("1. Get pending transactions")
        print("2. View Balance")
        print("3. Send Money")
        print("4. Request Money")
        print("5. Request refund")
        print("6. View all transactions")
        print('7. Add funds to wallet')
        print("8. Logout")
        # get user input
        choice = int(input('>'))
        if choice == 1:
            # fetch transactions
            print("Getting pending transactions")
            getPendingTransactions(cproto)
        elif choice == 2:
            getUserBalance(cproto)
        elif choice == 3:
            print("sending money")
            sendMoney(cproto)
        elif choice == 4:
            print("requesting money")
            requestMoney(cproto, 'REQUEST')
        elif choice == 5:
            requestRefund(cproto)
        elif choice == 6:
            viewAllTransactions(cproto)
        elif choice == 7:
            addFundsToWallet(cproto)
        elif choice == 8:
            logoutUser(cproto)
            loggedIn = False
        else:
            print("invalid choice")

def setCurrUser(msg):
    username = msg.getParam('username')
    userID = msg.getParam('id')
    CURR_USER["username"] = username
    CURR_USER["ID"] = userID
    print(f'[{userID}] {username} logged in successfully')


def loginClient(cproto: Cprotocol):
    username = input('Username: ')
    password = input('Password: ')
    m3 = Cmessage()
    m3.setType('LGIN')
    m3.addParam('username',username)
    m3.addParam('password', password)
    cproto.putMessage(m3)
    print(f'\n[SENT]:\t\t{m3}')
    m4 = cproto.getMessage()
    print(f'[RECIEVED]:\t{m4}')
    if m4.getType() == 'GOOD':
        setCurrUser(m4)
        return True
    else:
        print('\n')
        print(m4.getParam('message'))
        return False
