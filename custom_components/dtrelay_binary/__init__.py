"""Dingtian Binary Relay – Direct TCP/UDP Integration"""

import logging
from homeassistant import config_entries
from .const import DOMAIN
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass, entry: config_entries.ConfigEntry):
    data = entry.data
    host = data.get('host')
    listen_port = data.get('listen_port')
    send_port = data.get('send_port')
    protocol = data.get('protocol', 'UDP')
    sn_probe = bytes.fromhex(data.get('sn_request_hex') or '') if data.get('sn_request_hex') else None
    options = entry.options or {}

    _LOGGER.info('Setting up %s (%s) protocol=%s', entry.title, host, protocol)

    if protocol == 'UDP':
        from .helpers import DTRelayUDPHandler
        transport, protocol_obj = await hass.loop.create_datagram_endpoint(
            lambda: DTRelayUDPHandler(hass, entry.entry_id, host, send_port, sn_probe, options),
            local_addr=('0.0.0.0', listen_port)
        )
        hass.data[DOMAIN][entry.entry_id] = {'transport': transport, 'handler': protocol_obj}
    else:
        from .helpers import DTRelayTCPHandler
        handler = DTRelayTCPHandler(hass, entry.entry_id, host, listen_port, send_port, sn_probe, options)
        hass.loop.create_task(handler.start())
        hass.data[DOMAIN][entry.entry_id] = {'handler': handler}

    hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, 'binary_sensor'))
    hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, 'switch'))

    return True

async def async_unload_entry(hass, entry):
    info = hass.data[DOMAIN].pop(entry.entry_id, None)
    if not info:
        return True
    try:
        transport = info.get('transport')
        handler = info.get('handler')
        if transport:
            transport.close()
        if hasattr(handler, 'stop'):
            await handler.stop()
    except Exception:
        _LOGGER.exception('Error unloading entry')
    return True
