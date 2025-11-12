\
    import socket
    import logging
    import voluptuous as vol
    from homeassistant import config_entries
    from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT, CONF_PASSWORD
    from .const import DEFAULT_LOCKOUT_SECONDS, DEFAULT_PULSE_MS, DOMAIN
    import binascii

    _LOGGER = logging.getLogger(__name__)

    CONF_PROTOCOL = "protocol"
    CONF_PREFIX = "prefix"
    CONF_SERIAL = "serial_number"
    CONF_LANGUAGE = "language"
    CONF_LOCKOUT = "lockout_seconds"
    CONF_PULSE = "pulse_ms"

    ERRORS = {
        1250: "Unable to create UDP/TCP socket.",
        1255: "Network unreachable – invalid IP or port.",
        1258: "Device did not respond in time (1 s).",
        1260: "Invalid response from device.",
        1261: "Serial number must be 5 digits (0–9).",
        1265: "Unknown communication error."
    }

    class DTRelayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
        VERSION = 1
        CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

        async def async_step_user(self, user_input=None):
            errors = {}
            lang = "pl"
            if user_input and CONF_LANGUAGE in user_input:
                lang = user_input.get(CONF_LANGUAGE, "pl")

            # actions: fetch_sn, test_conn, submit
            if user_input is not None and user_input.get("action") == "fetch_sn":
                try:
                    sn = await self._async_fetch_sn(user_input)
                    if sn:
                        user_input[CONF_SERIAL] = sn
                    else:
                        errors["base"] = "1258"
                except DTRelayError as e:
                    _LOGGER.error("Fetch SN error %s: sent=%s recv=%s", e.code, e.sent_hex, e.recv_hex)
                    errors["base"] = str(e.code)
                return await self._show_form(user_input, errors, lang)

            if user_input is not None and user_input.get("action") == "test_conn":
                try:
                    ok = await self._async_test_connection(user_input)
                    if ok:
                        user_input["_test_ok"] = True
                    else:
                        errors["base"] = "1258"
                except DTRelayError as e:
                    _LOGGER.error("Test connection error %s: sent=%s recv=%s", e.code, e.sent_hex, e.recv_hex)
                    errors["base"] = str(e.code)
                return await self._show_form(user_input, errors, lang)

            if user_input is not None and user_input.get("action") == "submit":
                sn = user_input.get(CONF_SERIAL, "").strip()
                prefix = user_input.get(CONF_PREFIX, "DTRelay")[:10]
                if not sn or not sn.isdigit() or len(sn) != 5:
                    errors["base"] = "1261"
                    return await self._show_form(user_input, errors, lang)
                data = {
                    "protocol": user_input.get(CONF_PROTOCOL, "UDP"),
                    "host": user_input.get(CONF_IP_ADDRESS),
                    "listen_port": int(user_input.get(CONF_PORT)),
                    "send_port": int(user_input.get(CONF_PORT)),
                    "sn": sn,
                    "name": prefix,
                    "password": user_input.get(CONF_PASSWORD),
                    "lockout_seconds": int(user_input.get(CONF_LOCKOUT, DEFAULT_LOCKOUT_SECONDS)),
                    "pulse_ms": int(user_input.get(CONF_PULSE, DEFAULT_PULSE_MS)),
                    "language": lang,
                }
                title = f"{prefix}_{sn}"
                return self.async_create_entry(title=title, data=data)

            return await self._show_form(user_input, errors, lang)

        async def _show_form(self, user_input=None, errors=None, lang="pl"):
            errors = errors or {}
            defaults = {
                CONF_PROTOCOL: "UDP",
                CONF_IP_ADDRESS: "192.168.1.100",
                CONF_PORT: 60000,
                CONF_PASSWORD: "admin",
                CONF_PREFIX: "DTRelay",
                CONF_SERIAL: "",
                CONF_LOCKOUT: DEFAULT_LOCKOUT_SECONDS,
                CONF_PULSE: DEFAULT_PULSE_MS,
                CONF_LANGUAGE: lang,
            }
            if user_input:
                defaults.update(user_input)

            data_schema = vol.Schema({
                vol.Required(CONF_PROTOCOL, default=defaults[CONF_PROTOCOL]): vol.In(["UDP","TCP"]),
                vol.Required(CONF_IP_ADDRESS, default=defaults[CONF_IP_ADDRESS]): str,
                vol.Required(CONF_PORT, default=defaults[CONF_PORT]): int,
                vol.Required(CONF_PASSWORD, default=defaults[CONF_PASSWORD]): str,
                vol.Required(CONF_PREFIX, default=defaults[CONF_PREFIX]): str,
                vol.Required(CONF_SERIAL, default=defaults[CONF_SERIAL]): str,
                vol.Optional(CONF_LOCKOUT, default=defaults[CONF_LOCKOUT]): int,
                vol.Optional(CONF_PULSE, default=defaults[CONF_PULSE]): int,
                vol.Optional(CONF_LANGUAGE, default=defaults[CONF_LANGUAGE]): vol.In(["pl","en"]),
                vol.Optional("action", default=""): str,
            })

            return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors, description_placeholders={})

        async def _async_fetch_sn(self, user_input):
            ip = user_input.get(CONF_IP_ADDRESS)
            port = int(user_input.get(CONF_PORT))
            proto = user_input.get(CONF_PROTOCOL, "UDP").upper()

            try:
                if proto == "TCP":
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(1.0)
                    res = s.connect_ex((ip, port))
                    s.close()
                    if res != 0:
                        raise DTRelayError(1255, sent_hex="", recv_hex="")
                else:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.settimeout(1.0)
                    try:
                        s.sendto(b"", (ip, port))
                    except OSError:
                        s.close()
                        raise DTRelayError(1255, sent_hex="", recv_hex="")
                    s.close()
            except DTRelayError:
                raise
            except Exception:
                raise DTRelayError(1250, sent_hex="", recv_hex="")

            frame = bytes([0x05]) + bytes(33)
            sent_hex = binascii.hexlify(frame).decode()

            try:
                if proto == "UDP":
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.settimeout(1.0)
                    sock.sendto(frame, (ip, port))
                    try:
                        data, addr = sock.recvfrom(512)
                    except socket.timeout:
                        sock.close()
                        raise DTRelayError(1258, sent_hex=sent_hex, recv_hex="")
                    sock.close()
                else:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1.0)
                    sock.connect((ip, port))
                    sock.sendall(frame)
                    try:
                        data = sock.recv(512)
                    except socket.timeout:
                        sock.close()
                        raise DTRelayError(1258, sent_hex=sent_hex, recv_hex="")
                    sock.close()

                recv_hex = binascii.hexlify(data).decode()
                _LOGGER.debug("FIND response raw: %s", recv_hex)
                if len(data) >= 6 and data[0] == 0x05:
                    sn = int.from_bytes(data[2:6], "little")
                    return str(sn)
                else:
                    raise DTRelayError(1260, sent_hex=sent_hex, recv_hex=recv_hex)
            except DTRelayError:
                raise
            except Exception:
                raise DTRelayError(1265, sent_hex=sent_hex, recv_hex="")

        async def _async_test_connection(self, user_input):
            ip = user_input.get(CONF_IP_ADDRESS)
            port = int(user_input.get(CONF_PORT))
            proto = user_input.get(CONF_PROTOCOL, "UDP").upper()
            pwd = user_input.get(CONF_PASSWORD, "admin")

            frame = bytearray()
            frame.append(0xFF)
            frame.append(0x00 ^ 0xAA)
            frame.append(0x00)
            frame.append(0x00)
            frame.append(0x00)
            frame.append(0x00)
            sent_hex = binascii.hexlify(bytes(frame)).decode()

            try:
                if proto == "TCP":
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(1.0)
                    res = s.connect_ex((ip, port))
                    s.close()
                    if res != 0:
                        raise DTRelayError(1255, sent_hex=sent_hex, recv_hex="")
                else:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.settimeout(1.0)
                    try:
                        s.sendto(b"", (ip, port))
                    except OSError:
                        s.close()
                        raise DTRelayError(1255, sent_hex=sent_hex, recv_hex="")
                    s.close()
            except DTRelayError:
                raise
            except Exception:
                raise DTRelayError(1250, sent_hex=sent_hex, recv_hex="")

            try:
                if proto == "UDP":
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.settimeout(1.0)
                    sock.sendto(bytes(frame), (ip, port))
                    try:
                        data, addr = sock.recvfrom(512)
                    except socket.timeout:
                        sock.close()
                        raise DTRelayError(1258, sent_hex=sent_hex, recv_hex="")
                    sock.close()
                else:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1.0)
                    sock.connect((ip, port))
                    sock.sendall(bytes(frame))
                    try:
                        data = sock.recv(512)
                    except socket.timeout:
                        sock.close()
                        raise DTRelayError(1258, sent_hex=sent_hex, recv_hex="")
                    sock.close()

                recv_hex = binascii.hexlify(data).decode()
                _LOGGER.debug("TEST response raw: %s", recv_hex)
                if data and len(data) >= 4:
                    return True
                else:
                    raise DTRelayError(1260, sent_hex=sent_hex, recv_hex=recv_hex)
            except DTRelayError:
                raise
            except Exception:
                raise DTRelayError(1265, sent_hex=sent_hex, recv_hex="")

    class DTRelayError(Exception):
        def __init__(self, code, sent_hex="", recv_hex=""):
            self.code = code
            self.sent_hex = sent_hex
            self.recv_hex = recv_hex
            super().__init__(f"Error {code}")
