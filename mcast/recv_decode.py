# 1. receive multicast messages from WSJT-X
# 2. decode messages from QTDatastream and map the fields
#
# Format description:
# https://sourceforge.net/p/wsjt/wsjtx/ci/master/tree/Network/NetworkMessage.hpp
# based on QT QtDatastream.
# if using PyQt5, sudo apt install qtbase5-dev; pip install pyqt5
# if using PySide6, pip install pyside6

import socket
import struct
import sys
#from PyQt5.QtCore import QByteArray, QDataStream, QIODevice
from PySide6.QtCore import QByteArray, QDataStream, QIODevice

mcast_group = '224.0.0.1'
mcast_port = 2237

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((mcast_group, mcast_port))

mreq = socket.inet_aton(mcast_group) + socket.inet_aton("0.0.0.0")
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

while True:
    data, addr = sock.recvfrom(10240)
    print("Source: ",format(addr))
    buffer = QByteArray(data)
    stream = QDataStream(buffer)
    stream.setByteOrder(QDataStream.BigEndian)
    try:
        magic = stream.readUInt32()
        # print("magic: {magic}".format(magic=magic))
        if magic != 0xadbccbda:
            raise Exception("bad magic number ({magic})")
        schema = stream.readUInt32()
        if schema != 2:
            raise Exception("unsupported schema ({schema})")
        message_type = stream.readUInt32()
        id = stream.readUInt32()
        print("id: {id}".format(id=id))
        print("message type: {message_type} ".format(message_type=message_type), end='')

        match message_type:
            case 0: # heartbeat
                print ("(heartbeat)")
                max_schema = stream.readUInt32()
                print("max_schema: {max_schema}".format(max_schema=max_schema))
                version = stream.readUInt32()
                print("version: ".format(version=version))
                revision = stream.readUInt32()
                
    except Exception as e:
        print("Error decoding WSJT-X data:", str(e))
    print()