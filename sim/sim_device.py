#!/usr/bin/env python3
"""Simple UDP simulator for a DT-Relay device (responds to multicast find and SN probe)."""
import socket, time, struct
MCAST_GRP='224.0.2.11'
MCAST_PORT=60000
SN=12345
IP='127.0.0.1'

def build_find_response(sn=SN, ip='127.0.0.1'):
    # build 05 AA + 32-byte struct with sn,sw,hw,model,ip...
    pkt = bytearray()
    pkt.append(0x05)
    pkt.append(0xAA)
    # 32 bytes struct
    # sn, sw_ver, hw_ver, model, ip, netmask, gateway, dns
    pkt.extend(struct.pack('<I', sn))
    pkt.extend(struct.pack('<I', 0x0100))
    pkt.extend(struct.pack('<I', 0x0100))
    pkt.extend(struct.pack('<I', 16))
    ip_parts = [int(x) for x in ip.split('.')]
    ip_u = ip_parts[0] | (ip_parts[1]<<8) | (ip_parts[2]<<16) | (ip_parts[3]<<24)
    pkt.extend(struct.pack('<I', ip_u))
    pkt.extend(struct.pack('<I', 0xFFFFFF00))
    pkt.extend(struct.pack('<I', ip_u))
    pkt.extend(struct.pack('<I', ip_u))
    return bytes(pkt)

if __name__=='__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MCAST_PORT))
    # join multicast group
    mreq = struct.pack('4sl', socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    print('Simulator listening for probes...')
    while True:
        data, addr = sock.recvfrom(2048)
        print('Received', data, 'from', addr)
        if data[:1] == b'\x05' or data[:2] == b'\x05\xAA' or b'GET_SN' in data:
            resp = build_find_response()
            sock.sendto(resp, addr)
            print('Sent find response to', addr)
