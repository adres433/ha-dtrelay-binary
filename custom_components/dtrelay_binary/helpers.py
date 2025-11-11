"""Parser, frame builders, UDP/TCP handlers and discovery for Dingtian Binary Protocol."""

import struct, asyncio, logging, socket
from binascii import hexlify
from .const import MULTICAST_ADDR, DEFAULT_SEND_PORT

_LOGGER = logging.getLogger(__name__)

def _bits_from_le_bytes(bts, count=None):
    bits = []
    for byte in bts:
        for bit in range(8):
            bits.append(((byte >> bit) & 1) == 1)
    if count:
        return bits[:count]
    return bits

def _u32_le(bts, offset=0):
    try:
        return struct.unpack_from('<I', bts, offset)[0]
    except Exception:
        return 0

def _ip_from_u32(u):
    return '.'.join(str((u >> (8*i)) & 0xFF) for i in range(4))

def _parse_binary_frame(data_bytes):
    if not data_bytes or len(data_bytes) < 4:
        return None
    cmd = data_bytes[0]
    if cmd == 0x05 and len(data_bytes) >= 34:
        try:
            fd = data_bytes[2:2+32]
            sn = _u32_le(fd,0)
            sw_ver = _u32_le(fd,4)
            hw_ver = _u32_le(fd,8)
            model = _u32_le(fd,12)
            ip_u = _u32_le(fd,16)
            netmask_u = _u32_le(fd,20)
            gateway_u = _u32_le(fd,24)
            dns_u = _u32_le(fd,28)
            return {'type':'find','sn':str(sn),'sw_ver':sw_ver,'hw_ver':hw_ver,'model':model,'ip':_ip_from_u32(ip_u),'netmask':_ip_from_u32(netmask_u),'gateway':_ip_from_u32(gateway_u),'dns':_ip_from_u32(dns_u),'raw_hex': hexlify(data_bytes).decode()}
        except Exception as e:
            _LOGGER.debug('Find parse failed: %s', e)
            return None
    if len(data_bytes) < 6:
        return None
    result = data_bytes[1] ^ 0xAA
    session = data_bytes[2]
    relay_cmd = data_bytes[3]
    payload = data_bytes[6:]
    if relay_cmd == 0:
        if len(payload) >= 2:
            half = len(payload)//2
            relay_bytes = payload[:half]
            input_bytes = payload[half:half*2]
            channels = min(32, half*8)
            outputs = _bits_from_le_bytes(relay_bytes, channels)
            inputs = _bits_from_le_bytes(input_bytes, channels)
            return {'type':'status','session':session,'inputs':inputs,'outputs':outputs,'channels':channels,'raw_hex': hexlify(data_bytes).decode()}
        return None
    if relay_cmd == 4:
        try:
            if len(payload) >= 8:
                mac = ':'.join('{:02x}'.format(b) for b in payload[0:6])
                rest = payload[6:]
                half = len(rest)//2
                relay_bytes = rest[:half]
                input_bytes = rest[half:half*2]
                channels = min(32, half*8)
                outputs = _bits_from_le_bytes(relay_bytes, channels)
                inputs = _bits_from_le_bytes(input_bytes, channels)
                return {'type':'keepalive','mac':mac,'inputs':inputs,'outputs':outputs,'channels':channels,'raw_hex': hexlify(data_bytes).decode()}
        except Exception as e:
            _LOGGER.debug('Keepalive parse failed: %s', e)
            return None
    if relay_cmd in (1,2,3,8,9):
        return {'type':'ack','relay_cmd':relay_cmd,'session':session,'raw_hex': hexlify(data_bytes).decode()}
    return None

def build_write_relay_frame(session, password, relay_mask_bytes, set_bytes):
    frame = bytearray()
    frame.append(0xFF)
    frame.append(0x00 ^ 0xAA)
    frame.append(session & 0xFF)
    frame.append(0x01)
    frame.append(password & 0xFF)
    frame.append((password >> 8) & 0xFF)
    frame.extend(relay_mask_bytes)
    frame.extend(set_bytes)
    return bytes(frame)

class DTRelayUDPHandler(asyncio.DatagramProtocol):
    def __init__(self, hass, entry_id, device_ip, send_port, sn_probe, options=None):
        self.hass = hass
        self.entry_id = entry_id
        self.device_ip = device_ip
        self.send_port = send_port
        self.sn_probe = sn_probe
        self.transport = None
        self.options = options or {}

    def connection_made(self, transport):
        self.transport = transport
        if self.sn_probe:
            asyncio.get_event_loop().call_later(0.5, self._probe_sn)

    def datagram_received(self, data, addr):
        parsed = _parse_binary_frame(data)
        if parsed:
            parsed['entry_id'] = self.entry_id
            parsed['addr'] = addr
            self.hass.bus.async_fire('dtrelay_frame_received', parsed)
            return
        try:
            text = data.decode('utf-8', errors='ignore')
            if ':' in text:
                parts = text.strip().split(':')
                if len(parts) >= 3:
                    inp = parts[0].zfill(32)[:32]
                    outp = parts[1].zfill(32)[:32]
                    channels = int(parts[2]) if parts[2].isdigit() else 16
                    inputs = [c=='1' for c in inp[:channels]]
                    outputs = [c=='1' for c in outp[:channels]]
                    self.hass.bus.async_fire('dtrelay_frame_received', {'entry_id':self.entry_id,'inputs':inputs,'outputs':outputs,'raw':text,'addr':addr})
                    return
        except Exception:
            pass
        self.hass.bus.async_fire('dtrelay_frame_received', {'entry_id':self.entry_id,'raw_hex':hexlify(data).decode(),'addr':addr})

    def _probe_sn(self):
        if not self.transport or not self.device_ip:
            return
        try:
            self.transport.sendto(self.sn_probe, (self.device_ip, int(self.send_port)))
        except Exception:
            pass

class DTRelayTCPHandler:
    def __init__(self, hass, entry_id, host, listen_port, send_port, sn_probe, options=None):
        self.hass = hass
        self.entry_id = entry_id
        self.host = host
        self.listen_port = listen_port
        self.send_port = send_port
        self.sn_probe = sn_probe
        self.options = options or {}
        self.reader = None
        self.writer = None
        self._running = False

    async def start(self):
        self._running = True
        while self._running:
            try:
                reader, writer = await asyncio.open_connection(self.host, self.send_port)
                self.reader = reader
                self.writer = writer
                if self.sn_probe:
                    writer.write(self.sn_probe)
                    await writer.drain()
                while True:
                    data = await reader.read(4096)
                    if not data:
                        break
                    parsed = _parse_binary_frame(data)
                    if parsed:
                        parsed['entry_id'] = self.entry_id
                        self.hass.bus.async_fire('dtrelay_frame_received', parsed)
            except Exception:
                await asyncio.sleep(5)

    async def stop(self):
        self._running = False
        if self.writer:
            self.writer.close()
            try:
                await self.writer.wait_closed()
            except Exception:
                pass

async def discover_devices_multicast(sn_probe_hex, timeout=2.0, multicast_addr=MULTICAST_ADDR, port=DEFAULT_SEND_PORT):
    results = []
    loop = asyncio.get_event_loop()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(timeout)
    try:
        sock.bind(('', 0))
        sock.sendto(bytes.fromhex(sn_probe_hex), (multicast_addr, port))
        start = loop.time()
        while True:
            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                break
            parsed = _parse_binary_frame(data)
            if parsed and parsed.get('type') == 'find':
                parsed['addr'] = addr
                results.append(parsed)
            if loop.time() - start > timeout:
                break
    finally:
        sock.close()
    return results
