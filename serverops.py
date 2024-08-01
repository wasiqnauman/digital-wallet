import socket, threading
from cprotocol import Cprotocol
from cmessage import Cmessage
import sqlite3 as sqldb
from datetime import date, datetime

DATABASE = "./data.db"
CURR_USER = {}


def fetchAccList():
    conn = sqldb.connect(DATABASE)
    conn.row_factory = sqldb.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users;")
    # result = c.fetchall()
    result = [dict(row) for row in c.fetchall()]
    c.close()
    return result


def createWallet():
    latestAcc = fetchAccList()[-1]
    owner = latestAcc['id']
    balance = 300
    conn = sqldb.connect(DATABASE)
    conn.row_factory = sqldb.Row
    c = conn.cursor()
    data_tuple = (owner, balance)
    print(data_tuple)
    query = "INSERT INTO wallet(owner, balance) VALUES(?,?)"
    c.execute(query, data_tuple)
    conn.commit()
    c.close()

def createUser(cproto, msg):
    username = msg.getParam('username')
    password = msg.getParam('password')
    conn = sqldb.connect(DATABASE)
    conn.row_factory = sqldb.Row
    c = conn.cursor()
    data_tuple = (username, password)
    print(data_tuple)
    query = "INSERT INTO users(username, password) VALUES(?,?)"
    c.execute(query, data_tuple)
    conn.commit()
    c.close()
    createWallet()

    m = Cmessage()
    m.setType('GOOD')
    m.addParam('signup', 'successful')
    cproto.putMessage(m)

def sendMessageToClient(cproto, message):
    m = Cmessage()



def getAccIDList():
    accList = {acc["id"]:acc["username"] for acc in fetchAccList()}
    return accList

def getAccNameList():
    accList = {acc["username"]:acc["id"] for acc in fetchAccList()}
    return accList
    


def sendUserList(cproto: Cprotocol):
    accList = getAccIDList();
    m = Cmessage()
    m.setType('DATA')
    m.addParam('listSize', len(accList))
    cproto.putMessage(m)

    for id,username in accList.items():
        m = Cmessage()
        m.setType('DATA')
        m.addParam('id', id)
        m.addParam('username', username)
        cproto.putMessage(m)

    return accList

def fetchTransactions(cproto: Cprotocol):
    id = CURR_USER["id"]
    conn = sqldb.connect(DATABASE)
    conn.row_factory = sqldb.Row
    c = conn.cursor()
    query = "SELECT * FROM TRANSACTIONs WHERE author=? OR recipient=?;"
    params = (id,id,)
    c.execute(query, params)
    result = [dict(row) for row in c.fetchall()]
    c.close()
    return result

def getTransactions(cproto: Cprotocol):
    transactions = fetchTransactions(cproto)
    accList = getAccIDList()
    

    m = Cmessage()
    m.setType('DATA')
    m.addParam('listSize', len(transactions))
    cproto.putMessage(m)

    for t in transactions:
        # convert ID to name
        t["author"] = accList[t["author"]]
        t["recipient"] = accList[t["recipient"]]
        ID, FROM, TO, TYPE, STATUS, AMOUNT, CREATED, COMPLETED= t["id"], t["author"], t["recipient"], t["type"], t["status"], t["amount"], t["started"], t["completed"]
        m = Cmessage()
        m.setType('DATA')
        m.addParam('id', ID)
        m.addParam('to', TO)
        m.addParam('from', FROM)
        m.addParam('type', TYPE)
        m.addParam('status', STATUS)
        m.addParam('amount', AMOUNT)
        m.addParam('created', CREATED)
        m.addParam('completed', COMPLETED)
        cproto.putMessage(m)


def createTransaction(author, to, ttype, status, amount, message):
    # started = today.strftime("%m/%d/%y")
    now = datetime.now()
    started = now.strftime("%d/%m/%Y %H:%M:%S")
    conn = sqldb.connect(DATABASE)
    conn.row_factory = sqldb.Row
    c = conn.cursor()
    data_tuple = (author, to, ttype, status, amount, message, started)
    print(data_tuple)
    query = "INSERT INTO transactions(author, recipient, type, status, amount, message, started) VALUES(?,?,?,?,?,?,?);"
    c.execute(query, data_tuple)
    conn.commit()
    c.close()

def sendMoneyToUser(cproto: Cprotocol, msg):
    to = int(msg.getParam('to'))
    amount = int(msg.getParam('amount'))
    author = CURR_USER["id"]
    message = msg.getParam('message')
    status = 'PENDING'
    ttype = 'SEND'
    createTransaction(author, to, ttype, status, amount, message)
    print("transaction created")

def updateWalletBalance(owner, amount):
    conn = sqldb.connect(DATABASE)
    conn.row_factory = sqldb.Row
    c = conn.cursor()
    # transfer funds
    query = "UPDATE wallet SET balance=balance + ? WHERE owner=?;"
    params = (amount, owner)
    c.execute(query, params)
    conn.commit()
    c.close()

def updateTransaction(tID, status):
    conn = sqldb.connect(DATABASE)
    conn.row_factory = sqldb.Row
    c = conn.cursor()
    # completed = today.strftime("%m/%d/%y")
    now = datetime.now()
    completed = now.strftime("%d/%m/%Y %H:%M:%S")
    query = "UPDATE transactions SET status=?,completed=?  WHERE ID=?;"
    params = (status, completed, tID)
    c.execute(query, params)
    conn.commit()
    c.close()


def requestRefund(cproto, msg):
    accNameList = getAccNameList()
    to = accNameList[msg.getParam('to')]
    author = accNameList[msg.getParam('from')]
    print(to, author)
    amount = int(msg.getParam('amount'))
    tID = int(msg.getParam('tID'))
    flag = msg.getParam('flag')
    ttype = msg.getParam('ttype')
    status = "PENDING"
    message = msg.getParam('message')
    createTransaction(author, to, ttype, status, amount, message)
    print("transaction created")

def requestFunds(cproto, msg):
    to = int(msg.getParam('to'))
    amount = int(msg.getParam('amount'))
    author = CURR_USER["id"]
    message = msg.getParam('message')
    status = 'PENDING'
    ttype = msg.getParam('ttype')
    createTransaction(author, to, ttype, status, amount, message)
    print("transaction created")

def transferFunds(cproto, msg):
    accNameList = getAccNameList()
    to = accNameList[msg.getParam('to')]
    author = accNameList[msg.getParam('from')]
    print(to, author)
    amount = int(msg.getParam('amount'))
    tID = int(msg.getParam('tID'))
    flag = msg.getParam('flag')
    ttype = msg.getParam('ttype')

    # if the transaction is cancelled or denied then just update the flag and close the transaction
    if flag != 'ACCEPTED':
        updateTransaction(tID, flag)
        return
    
    if ttype == 'REQUEST' or ttype == 'REFUND':
        (to, author) = (author, to)
    print(msg.getType(), to, author)
    owner, ownerBalance = getWalletData(author)
    if ownerBalance - amount >= 0:
        updateWalletBalance(author, -amount)
        updateWalletBalance(to, amount)
        updateTransaction(tID, 'COMPLETED')
        print("Funds Successfully Transferred")
    else:
        print("Insufficient funds to transfer")

    

    

def fetchWalletList():
    conn = sqldb.connect(DATABASE)
    conn.row_factory = sqldb.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users;")
    # result = c.fetchall()
    result = [dict(row) for row in c.fetchall()]
    c.close()
    print(result)
    return result

def getWalletData(id):
    conn = sqldb.connect(DATABASE)
    conn.row_factory = sqldb.Row
    c = conn.cursor()
    query = "SELECT * FROM wallet WHERE owner=?;"
    params = (id,)
    c.execute(query, params)
    # result = c.fetchall()
    result = [dict(row) for row in c.fetchall()]
    c.close()
    
    owner, balance = result[0]["owner"], result[0]["balance"]
    print(owner, balance)
    return owner, balance

def setCurrUser(acc: dict):
    CURR_USER["username"] = acc["username"]
    CURR_USER["id"] = acc["id"]
    CURR_USER["password"] = acc["password"]
    print(f'{CURR_USER} connected to the server')


def saveSession():
    owner, balance = getWalletData(CURR_USER["id"])
    with open('userInfo.txt', 'w') as f:
        f.write(f'{CURR_USER["id"]} {CURR_USER["username"]} {balance}')
    
def viewBalance(cproto: Cprotocol, msg: Cmessage):
    user = CURR_USER["username"]
    print(f'Get wallet balance for: {user}')
    owner, balance = getWalletData(CURR_USER["id"])
    m = Cmessage()
    m.setType('DATA')
    m.addParam('user', user)
    m.addParam('balance', balance)
    cproto.putMessage(m)
    return balance

def loginUser(cproto: Cprotocol, name: str, pwd: str) -> int:
    accList = fetchAccList()
    # this is for the case the user exists
    for acc in accList:
        if acc["username"] == name:
            if acc["password"] == pwd:
                m = Cmessage()
                m.setType('GOOD')
                m.addParam('Login', 'Successful')
                m.addParam('username', acc["username"])
                m.addParam('id', acc["id"])
                cproto.putMessage(m)
                setCurrUser(acc)
                return 1
            else:
                m = Cmessage()
                m.setType('ERRO')
                m.addParam('Login', 'Failed')
                m.addParam('message','incorrect password')
                cproto.putMessage(m)
                return 0
    # in the case that the user does not exist
    print("User not found")
    m = Cmessage()
    m.setType('ERRO')
    m.addParam('Login', 'Failed')
    m.addParam('message','User not found!')
    cproto.putMessage(m)


