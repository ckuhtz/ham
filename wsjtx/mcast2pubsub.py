# 1. receive multicast messages from WSJT-X (and anything that looks like it on the same group)
# 2. decode messages from QTDatastream and map the fields
# 3. ignore everything that isn't emitted by WSJT-X (although debug will show that
#    it has been seen on the wire)
# 4. emit to pubsub topic node/component/message_type
#
# format description:
# https://sourceforge.net/p/wsjt/wsjtx/ci/master/tree/Network/NetworkMessage.hpp
# based on QDatastream from the Qt framework.
#
# dependencies:
# if using PySide6, pip install pyside6
# if using PyQt5, sudo apt install qtbase5-dev; pip install pyqt5
# install hexdump with pip install simple-hexdump
# install juliandate with pip install juliandate
# install kombu for AMQP messaging
# install librabbitmq for high perf transport (optional)

import socket
import struct
import sys
from PySide6.QtCore import QByteArray, QDataStream, QIODevice
#from PyQt5.QtCore import QByteArray, QDataStream, QIODevice
from hexdump import hexdump
import datetime
import juliandate as jd
from kombu import Connection, Exchange, Producer

# constants

debug = True
debug_only_message_type = -1 # ignore specific message, all messages
debug_only_message_type = 0 # specific message only, cut down on the noise

amqp_url = "amqp://admin:admin@docker:5672/"

# decode the UTF-8 strings embedded in the QDatastream of WSJT-X UDP messages

def decode_utf8_str(stream):
    len = stream.readUInt32()
    if len == 0xffffffff: # null string is mashed into an empty string
        return ""
    else:
        bytes = stream.readRawData(len)
        return bytes.decode("utf-8)")

# decode qtime (milliseconds since midnight UTC) into an ISO 8601 timestamp string

def decode_qtime_iso8601str(stream):
    utcnow = datetime.datetime.now(datetime.UTC)
    utcmidnight = datetime.datetime(utcnow.year, utcnow.month, utcnow.day, 0, 0)
    msecs_since_midnight = stream.readUInt32()
    timestamp = utcmidnight + datetime.timedelta(milliseconds=msecs_since_midnight)
    iso8601_timestamp = timestamp.isoformat() + 'Z'
    
    if (debug and debug_only_message_type == -1):
        print("iso8601_timestamp:", iso8601_timestamp)

    return iso8601_timestamp

# decode qdatetime into an ISO 8601 timestamp string

def decode_qdatetime_iso8601str(stream):
    julian_days = stream.readInt64() # QDate
    msecs_since_midnight = stream.readUInt32()
    timespec = stream.readUInt8()
    if timespec == 3:
        raise("non-spec qso logged message received with timespec 3 (timezones).")
    if timespec == 2:
        offset = stream.readInt32()
        if debug:
                print("offset:", offset)
        raise("unable to deal with QDateTime objects with timespec=2 (offset={}).".format(offset))
            
    gregorian_datetime = datetime.datetime(*jd.to_gregorian(julian_days))

    # Apparently this is always noon. since the QTime is milliseconds since midnight, if we add it to the 
    # gregorgian_date the resulting timestamp will be off by 12 hours every time.
    # Instead, we recreate the date with starting point at midnight and add milliseconds to it.  This is safe
    # because julian_days will always be an integer and never fractions of a day.
    combined_datetime = datetime.datetime(gregorian_datetime.year, gregorian_datetime.month, gregorian_datetime.day,0,0) + datetime.timedelta(milliseconds=msecs_since_midnight)
    iso8601_datetime = combined_datetime.isoformat() + 'Z'

    if (debug and debug_only_message_type == -1):
        print("julian_days:", julian_days)
        print("msecs_since_midnight:", msecs_since_midnight)
        print("timespec:", timespec)
        print("gregorian_datetime:", gregorian_datetime)
        print("combined_datetime:", combined_datetime)
        print("combined_datetime.isoformat()Z:", iso8601_datetime)
        print("iso8601_datetime", iso8601_datetime)
    
    return iso8601_datetime

# set up AMQP producer

# FIXME
# https://github.com/ckuhtz/ham/issues/5

try:
    amqp_connection = Connection(amqp_url)
    if debug:
        print("AMQP URL:", amqp_url)
    amqp_channel = amqp_connection.channel()
    amqp_exchange_name = "wsjtx"
    amqp_exchange = Exchange(amqp_exchange_name, type='direct')
    if debug:
        print("AMQP exchange:", amqp_exchange_name)
    amqp_routing_key = "wsjtx-out"
    amqp_producer = Producer(
        exchange=amqp_exchange,
        channel=amqp_channel,
        routing_key=amqp_routing_key
    )
    if debug:
        print("AMQP routing key:", amqp_routing_key)
except Exception as e:
    print("AMQP init problem:", str(e))

if debug:
    print("AMQP init done. (maybe? see https://github.com/ckuhtz/ham/issues/5)")
    print()

# open multicast socket and join group 224.0.0.1:2237 where we expect WSJT-X UDP multicasts in QTDatastream format

mcast_group = '224.0.0.1'
mcast_port = 2237

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((mcast_group, mcast_port))

mreq = socket.inet_aton(mcast_group) + socket.inet_aton("0.0.0.0")
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

while True:
    # amqp_message is the object that is published to AMQP
    # it is reset to undefined here, and every message type that does publish a producer
    # message will provide its own message.  If undefined type is published, we know we hit
    # an area of the code that should be evaluated for more work.

    amqp_message = { 'type': 'undefined' }

    data, addr = sock.recvfrom(10240)
    
    buffer = QByteArray(data)
    stream = QDataStream(buffer)
    stream.setByteOrder(QDataStream.BigEndian)

    try:
        # check magic number match
        magic = stream.readUInt32()
        if magic != 0xadbccbda:
            if debug:
                print(hexdump(data))
                print("source:",format(addr))
            raise Exception("bad magic number (" + str(magic) + ")")
        
        # check schema number match
        schema = stream.readUInt32()
        if schema != 2:
            if debug:
                print(hexdump(data))
                print("source:",format(addr))
            raise Exception("unsupported schema (" + str(schema) + ")")

        # if we got here, we know we have something that looks like the message we're expecting from WSJT-X
        # or something that's acting like it

        message_type = stream.readUInt32()

        if ( debug and ( debug_only_message_type == -1 or debug_only_message_type == message_type )):
            print(hexdump(data))
            print("source:",format(addr))
    
        # FIXME
        # https://github.com/ckuhtz/ham/issues/3

        id = decode_utf8_str(stream)
        match message_type:
            case 0: 
                # Heartbeat message from WSJT-X (discovery and schema negotiation)
                # It appears schema negotation is optional?
                # Out/In
                max_schema = stream.readUInt32()
                version = decode_utf8_str(stream)
                revision = decode_utf8_str(stream)

                if ( debug and ( debug_only_message_type == -1 or debug_only_message_type == message_type )):
                    print("id:", id)
                    print("message_type: {message_type} ".format(message_type=message_type), end="")
                    print("(heartbeat)")
                    print("max_schema:", max_schema)
                    print ("version/revision: {version}/{revision}".format(version=version,revision=revision))

            case 1: 
                # Status update from WSJT-X
                # Out
                dial_freq = stream.readUInt64()
                mode = decode_utf8_str(stream)
                dx_call = decode_utf8_str(stream)
                report = decode_utf8_str(stream)
                tx_mode = decode_utf8_str(stream)
                tx_enabled = stream.readBool()
                transmitting = stream.readBool()
                decoding = stream.readBool()
                rx_df = stream.readUInt32()
                tx_df = stream.readUInt32()
                de_call = decode_utf8_str(stream)
                de_grid = decode_utf8_str(stream)
                dx_grid = decode_utf8_str(stream)
                tx_watchdog = stream.readBool()
                sub_mode = decode_utf8_str(stream)
                fast_mode = stream.readBool()
                spec_op_mode = stream.readUInt8()
                freq_tolerance = stream.readUInt32()
                tr_period = stream.readUInt32()
                config_name = decode_utf8_str(stream)
                tx_message = decode_utf8_str(stream)
                if ( debug and ( debug_only_message_type == -1 or debug_only_message_type == message_type )):
                    print("id:", id)
                    print("message_type: {message_type} ".format(message_type=message_type), end="")
                    print("(status)")
                    print("dial_freq:", dial_freq)
                    print("mode:", mode)
                    print("dx_call:", dx_call)
                    print("report:", report)
                    print("tx_mode:", tx_mode)
                    print("tx_enabled:", tx_enabled)
                    print("transmitting:", transmitting)
                    print("decoding:", decoding)
                    print("rx_df:", rx_df)
                    print("tx_df:", tx_df)
                    print("de_call:", de_call)
                    print("de_grid:", de_grid)
                    print("dx_grid:", dx_grid)
                    print("tx_watchdog:", tx_watchdog)
                    print("sub_mode:", sub_mode)
                    print("fast_mode:", fast_mode)
                    print("spec_op_mode: {} ".format(spec_op_mode), end="")
                    match spec_op_mode:
                        case 0:
                            print("(none)")
                        case 1:
                            print("(NA VHF)")
                        case 2:
                            print("(EU VHF)")
                        case 3:
                            print("(FIELD DAY)")
                        case 4:
                            print("(RTTY RU)")
                        case 5:
                            print("(WW DIGI)")
                        case 6:
                            print("(FOX)")
                        case 7:
                            print("(HOUND)")
                        case 8:
                            print("(ARRL DIGI)")
                        case _:
                            print("(wtf?)")
                    print("freq_tolerance:", freq_tolerance, end="")
                    if freq_tolerance == 4294967295:
                        print(" (not applicable)")
                    else:
                        print()
                    print("tr_period:", tr_period, end="")
                    if tr_period == 4294967295:
                        print(" (not applicable)")
                    else:
                        print()
                    print("config_name:", config_name)
                    print("tx_message:",tx_message)

            case 2: 
                # WSJT-X has decoded a message
                # Out
                new = stream.readBool()
                time = decode_qtime_iso8601str(stream)
                snr = stream.readInt32()
                delta_time = stream.readFloat()
                delta_freq = stream.readUInt32()
                mode = decode_utf8_str(stream)
                rx_message = decode_utf8_str(stream)
                low_conf = stream.readBool()
                off_air = stream.readBool()

                if ( debug and ( debug_only_message_type == -1 or debug_only_message_type == message_type )):
                    print("id:", id)
                    print("message_type: {message_type} ".format(message_type=message_type), end="")
                    print("(decode)")
                    print("new:", new)
                    print("time:", time)
                    print("snr:", snr)
                    print("delta_time:", delta_time)
                    print("delta_freq:", delta_freq)
                    print("mode:", mode)
                    print("rx_message:", rx_message)
                    print("low_conf:", low_conf)
                    print("off_air:", off_air)
                    
            case 3: 
                # Either user has discarded prior decodes or the server is being instructed to discard decodes
                # Out/In
                window = stream.readUInt8()

                if ( debug and ( debug_only_message_type == -1 or debug_only_message_type == message_type )):
                    print("id:", id)
                    print("message_type: {message_type} ".format(message_type=message_type), end="")
                    print("(clear)")
                    print("window:", window)

            case 4: 
                # Inbound control message to WSJT-X only
                # In

                if ( debug and ( debug_only_message_type == -1 or debug_only_message_type == message_type )):
                    print("id:", id)
                    print("message_type: {message_type} ".format(message_type=message_type), end="")
                    print("(reply)")

                # ignored

            case 5: # QSO logged
                datetime_off = decode_qdatetime_iso8601str(stream)
                dx_call = decode_utf8_str(stream)
                dx_grid = decode_utf8_str(stream)
                tx_freq = stream.readUInt64()
                mode = decode_utf8_str(stream)
                report_sent = decode_utf8_str(stream)
                report_rcvd = decode_utf8_str(stream)
                tx_power = decode_utf8_str(stream)
                comments = decode_utf8_str(stream)
                name = decode_utf8_str(stream)
                datetime_on = decode_qdatetime_iso8601str(stream)
                op_call = decode_utf8_str(stream)
                de_call = decode_utf8_str(stream)
                de_grid = decode_utf8_str(stream)
                exch_sent = decode_utf8_str(stream)
                exch_rcvd = decode_utf8_str(stream)
                adif_prop_mode = decode_utf8_str(stream)

                if ( debug and ( debug_only_message_type == -1 or debug_only_message_type == message_type )):
                    print("id:", id)
                    print("message_type: {message_type} ".format(message_type=message_type), end="")
                    print("(qso logged)")
                    print("datetime_off:", datetime_off)
                    print("dx_call:", dx_call)
                    print("dx_grid:", dx_grid)
                    print("tx_freq:", tx_freq)
                    print("mode:", mode)
                    print("report_sent:", report_sent)
                    print("report_rcvd:", report_rcvd)
                    print("tx_power:", tx_power)
                    print("comments:", comments)
                    print("name:", name)
                    print("datetime_on:", datetime_on)
                    print("op_call", op_call)
                    print("de_call:", de_call)
                    print("de_grid:", de_grid)
                    print("exch_sent:", exch_sent)
                    print("exch_rcvd:", exch_rcvd)
                    print("adif_prop_mode:", adif_prop_mode)

            case 6:
                # WSJT-X shutting down
                
                if ( debug and ( debug_only_message_type == -1 or debug_only_message_type == message_type )):
                    print("id:", id)
                    print("message_type: {message_type} ".format(message_type=message_type), end="")
                    print("(close)")

            case 7:
                # Replay previous band decodes from WSJT-X

                if ( debug and ( debug_only_message_type == -1 or debug_only_message_type == message_type )):
                    print("id:", id)
                    print("message_type: {message_type} ".format(message_type=message_type), end="")
                    print("(replay)")

                # ignored

            case 8:
                # Halt transmissions in WSJT-X
                # In

                if ( debug and ( debug_only_message_type == -1 or debug_only_message_type == message_type )):
                    print("id:", id)
                    print("message_type: {message_type} ".format(message_type=message_type), end="")
                    print("(halt tx)")
                
                # ignored

            case 9:
                # Set free text message in WSJT-X
                # In

                if ( debug and ( debug_only_message_type == -1 or debug_only_message_type == message_type )):
                    print("id:", id)
                    print("message_type: {message_type} ".format(message_type=message_type), end="")
                    print("(freetext)")
                
                # ignored
                    
            case 10:
                # WSPR decode receive from WSJT-X
                # Out
                
                if ( debug and ( debug_only_message_type == -1 or debug_only_message_type == message_type )):
                    print("id:", id)
                    print("message_type: {message_type} ".format(message_type=message_type), end="")
                    print("(WSPR decode)")
                
                # ignored

            case 11:
                # Location update for WSJT-X
                # In
                
                if ( debug and ( debug_only_message_type == -1 or debug_only_message_type == message_type )):
                    print("id:", id)
                    print("message_type: {message_type} ".format(message_type=message_type), end="")
                    print("(location update)")
                
                # ignored

            case 12: 
                # Logged ADIF message from WSJT-X
                # Out
                adif = decode_utf8_str(stream)
                
                if ( debug and ( debug_only_message_type == -1 or debug_only_message_type == message_type )):
                    print("id:", id)
                    print("message_type: {message_type} ".format(message_type=message_type), end="")
                    print("(logged ADIF)")
                    print("adif:", adif)

            case 13:
                # Highlight call sign in WSJT-X
                # In
                
                if ( debug and ( debug_only_message_type == -1 or debug_only_message_type == message_type )):
                    print("id:", id)
                    print("message_type: {message_type} ".format(message_type=message_type), end="")
                    print("(callsign highlight)")
                
                # ignored

            case 14:
                # Switch WSJT-X configuration
                # In

                if ( debug and ( debug_only_message_type == -1 or debug_only_message_type == message_type )):
                    print("id:", id)
                    print("message_type: {message_type} ".format(message_type=message_type), end="")
                    print("(switch configuration)")
                
                # ignored

            case 15:
                # Configure WSJT-X
                # In

                if ( debug and ( debug_only_message_type == -1 or debug_only_message_type == message_type )):
                    print("id:", id)
                    print("message_type: {message_type} ".format(message_type=message_type), end="")
                    print("(configure)")

                # ignored
                    
            case _:
                print()
                raise Exception("unknown message type " + str(id) + " received.")

    except Exception as e:
        print("Error decoding WSJT-X data:", str(e))
        
    # publish message to AMQP
        
    amqp_producer.publish(
        amqp_message,
        retry=False
    )
    if ( debug and ( debug_only_message_type == -1 or debug_only_message_type == message_type )):
        print("AMQP published ({})".format(message_type))
        print(">>", amqp_message)

    # if we're debugging, lets make sure we print a blank line to break up the mess. ;-) 

    if ( debug and ( debug_only_message_type == -1 or debug_only_message_type == message_type )):
        print()
