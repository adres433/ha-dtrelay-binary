import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, DEFAULT_LISTEN_PORT, DEFAULT_SEND_PORT, DEFAULT_SN_REQUEST_HEX, MULTICAST_ADDR, DEFAULT_LOCKOUT_SECONDS, DEFAULT_PULSE_MS
import socket, binascii, struct

CONF_LISTEN_PORT = 'listen_port'
CONF_SEND_PORT = 'send_port'
CONF_PROTOCOL = 'protocol'
CONF_SN_REQUEST_HEX = 'sn_request_hex'
CONF_USERNAME = 'username'
CONF_PASSWORD = 'password'
CONF_LOCKOUT = 'lockout_seconds'
CONF_PULSE = 'pulse_ms'

class DTRelayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is None:
            return self.async_show_form(
                step_id='user',
                data_schema=vol.Schema({
                    vol.Required('host', default='192.168.1.100'): str,
                    vol.Required(CONF_LISTEN_PORT, default=DEFAULT_LISTEN_PORT): int,
                    vol.Required(CONF_SEND_PORT, default=DEFAULT_SEND_PORT): int,
                    vol.Required(CONF_PROTOCOL, default='UDP'): vol.In(['UDP','TCP']),
                    vol.Optional('name', default='DTRelay'): str,
                    vol.Optional(CONF_SN_REQUEST_HEX, default=DEFAULT_SN_REQUEST_HEX): str,
                    vol.Optional(CONF_USERNAME, default=''): str,
                    vol.Optional(CONF_PASSWORD, default=''): str,
                    vol.Optional(CONF_LOCKOUT, default=DEFAULT_LOCKOUT_SECONDS): int,
                    vol.Optional(CONF_PULSE, default=DEFAULT_PULSE_MS): int,
                })
            )

        host = user_input.get('host')
        listen_port = int(user_input.get(CONF_LISTEN_PORT))
        send_port = int(user_input.get(CONF_SEND_PORT))
        proto = user_input.get(CONF_PROTOCOL)
        sn_hex = user_input.get(CONF_SN_REQUEST_HEX) or DEFAULT_SN_REQUEST_HEX
        sn_probe = binascii.unhexlify(sn_hex)
        lockout = int(user_input.get(CONF_LOCKOUT, DEFAULT_LOCKOUT_SECONDS))
        pulse_ms = int(user_input.get(CONF_PULSE, DEFAULT_PULSE_MS))

        sn = None
        try:
            if proto == 'UDP':
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(1.0)
                s.sendto(sn_probe, (host, send_port))
                data, _ = s.recvfrom(1024)
                s.close()
            else:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1.0)
                s.connect((host, send_port))
                s.sendall(sn_probe)
                data = s.recv(1024)
                s.close()
            txt = data.decode('utf-8', errors='ignore')
            if 'SN' in txt.upper():
                import re
                m = re.search(r'SN[:=\s]*([0-9A-Za-z\-]+)', txt, re.IGNORECASE)
                if m:
                    sn = m.group(1)
            if not sn and len(data) >= 34 and data[0] == 0x05:
                sn_val = struct.unpack_from('<I', data, 2)[0]
                sn = str(sn_val)
        except Exception:
            pass

        if not sn:
            errors['base'] = 'no_sn'
            return self.async_show_form(
                step_id='user',
                data_schema=vol.Schema({
                    vol.Required('host', default=host): str,
                    vol.Required(CONF_LISTEN_PORT, default=listen_port): int,
                    vol.Required(CONF_SEND_PORT, default=send_port): int,
                    vol.Required(CONF_PROTOCOL, default=proto): vol.In(['UDP','TCP']),
                    vol.Required('serial'): str,
                    vol.Optional('name', default=user_input.get('name','')): str,
                    vol.Optional(CONF_SN_REQUEST_HEX, default=sn_hex): str,
                    vol.Optional(CONF_USERNAME, default=''): str,
                    vol.Optional(CONF_PASSWORD, default=''): str,
                    vol.Optional(CONF_LOCKOUT, default=lockout): int,
                    vol.Optional(CONF_PULSE, default=pulse_ms): int,
                }),
                errors=errors
            )

        title = f"{user_input.get('name') or 'DTRelay'}_{sn}"
        entry_data = {
            'host': host,
            'listen_port': listen_port,
            'send_port': send_port,
            'protocol': proto,
            'sn': sn,
            'name': user_input.get('name') or 'DTRelay',
            'sn_request_hex': sn_hex,
            'username': user_input.get(CONF_USERNAME,'') or None,
            'password': user_input.get(CONF_PASSWORD,'') or None,
            'lockout_seconds': lockout,
            'pulse_ms': pulse_ms,
        }
        return self.async_create_entry(title=title, data=entry_data)

    async def async_step_discover(self, user_input=None):
        from .helpers import discover_devices_multicast
        await self.async_set_unique_id('dtrelay_discovery')
        if user_input is None:
            results = await discover_devices_multicast(DEFAULT_SN_REQUEST_HEX, timeout=2.0, multicast_addr=MULTICAST_ADDR, port=DEFAULT_SEND_PORT)
            if not results:
                return self.async_show_form(step_id='discover', description_placeholders={'count': 0}, data_schema=vol.Schema({}), errors={'base':'no_devices'})
            choices = {str(i): f"SN {r['sn']} @ {r.get('ip')} (model {r.get('model')})" for i, r in enumerate(results)}
            self._discover_results = results
            return self.async_show_form(step_id='discover', data_schema=vol.Schema({vol.Required('choice'): vol.In(choices)}))
        idx = int(user_input.get('choice'))
        picked = self._discover_results[idx]
        title = f"DTRelay_{picked['sn']}"
        entry_data = {
            'host': picked.get('ip'),
            'listen_port': DEFAULT_LISTEN_PORT,
            'send_port': DEFAULT_SEND_PORT,
            'protocol': 'UDP',
            'sn': picked.get('sn'),
            'name': title,
            'sn_request_hex': DEFAULT_SN_REQUEST_HEX,
            'username': None,
            'password': None,
            'lockout_seconds': DEFAULT_LOCKOUT_SECONDS,
            'pulse_ms': DEFAULT_PULSE_MS,
        }
        return self.async_create_entry(title=title, data=entry_data)
