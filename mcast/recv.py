# Receive multicast messages from WSJT-X
# Format description:
# https://sourceforge.net/p/wsjt/wsjtx/ci/master/tree/Network/NetworkMessage.hpp
# based on QT QtDatastream.


import socket
import struct
import sys

mcast_group = '224.0.0.1'
mcast_port = 2237

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', mcast_port))

mreq = struct.pack("4sl", socket.inet_aton(mcast_group), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

while True:
    data, addr = sock.recvfrom(1024)
    print("Received data from {}: {}".format(addr, data))

