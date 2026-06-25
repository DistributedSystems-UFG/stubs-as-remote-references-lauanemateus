import pickle, os           #-
from socket   import *      #-
from constRPC import *      #-
#-
class Client:
  def __init__(self, port, host=CLIENT_BIND_HOST):
    self.host = host                      # local bind interface
    self.port = port                      # port it will listen to
    self.sock = socket()                  # socket for incoming calls
    self.sock.bind((self.host, self.port))# bind socket to an address
    self.sock.listen(2)                   # max num connections

  def sendTo(self, host, port, data):
    sock = socket()
    sock.connect((host, port))            # connect to receiver (blocking call)
    sock.send(pickle.dumps(data))         # send marshaled data
    sock.close()

  def recvAny(self):
    (conn, addr) = self.sock.accept()
    data = conn.recv(1024)
    conn.close()
    return data
