import re
import datetime
import time
 
ADIF_REC_RE = re.compile(r'<(.*?):(\d+).*?>([^<\t\f\v]+)')
 
def parse(fn):
    raw = re.split('<eor>|<eoh>(?i)', open(fn).read() )
    logbook =[]
    for record in raw[1:-1]:
        qso = {}
        tags = ADIF_REC_RE.findall(record)
        for tag in tags:
                qso[tag[0].lower()] = tag[2][:int(tag[1])]
        logbook.append(qso)    
    return logbook
 
def save(fn, data):
    fh=open(fn,'w')
    fh.write('ADIF.PY by OK4BX\nhttp://web.bxhome.org\n<EOH>\n')
    for qso in data:
        for key in sorted(qso):
            value = qso[key]
            fh.write('<%s:%i>%s  ' % (key.upper(), len(value), value))
        fh.write('<EOR>\n')
    fh.close()
 
def conv_datetime(adi_date, adi_time):
    return datetime.datetime.strptime(adi_date+adi_time.ljust(6,"0"), "%Y%m%d%H%M%S")
 