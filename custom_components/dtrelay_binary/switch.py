from homeassistant.components.switch import SwitchEntity
from .const import MAX_CHANNELS
import socket, logging, asyncio
from .helpers import build_write_relay_frame

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    entry_id = entry.entry_id
    data = entry.data
    switches = [DTRelayOutput(hass, entry_id, i, data) for i in range(MAX_CHANNELS)]
    async_add_entities(switches, True)

class DTRelayOutput(SwitchEntity):
    def __init__(self, hass, entry_id, index, entry_data):
        self._hass = hass
        self._entry_id = entry_id
        self._index = index
        self._attr_name = f"{entry_data.get('name')}_{entry_data.get('sn')}_out{index+1}"
        self._attr_unique_id = f"{entry_id}_out_{index+1}"
        self._state = False
        self._device_ip = entry_data.get('host')
        self._send_port = entry_data.get('send_port')
        self._password = int(entry_data.get('password') or 0)
        self._session = 0
        self._lockout_seconds = int(entry_data.get('lockout_seconds') or 30)
        self._pulse_ms = int(entry_data.get('pulse_ms') or 200)
        self._last_action_time = 0
        hass.bus.async_listen('dtrelay_frame_received', self._update)

    def _update(self, event):
        if event.data.get('entry_id') != self._entry_id:
            return
        outputs = event.data.get('outputs')
        if outputs and len(outputs) > self._index:
            new = outputs[self._index]
            if new != self._state:
                self._state = new
                self.schedule_update_ha_state()

    @property
    def is_on(self):
        return self._state

    async def async_turn_on(self, **kwargs):
        await self._send_command(1)

    async def async_turn_off(self, **kwargs):
        await self._send_command(0)

    async def _send_command(self, value):
        now = asyncio.get_event_loop().time()
        if now - self._last_action_time < self._lockout_seconds:
            _LOGGER.debug('Lockout active for %s (%.1fs left)', self._attr_unique_id, self._lockout_seconds - (now - self._last_action_time))
            return
        idx = self._index
        mask = [0,0,0,0]
        setb = [0,0,0,0]
        byte_index = idx // 8
        bit = idx % 8
        mask[byte_index] = 1 << bit
        if value:
            setb[byte_index] = 1 << bit
        frame = build_write_relay_frame(self._session, self._password, bytes(mask), bytes(setb))
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1)
            sock.sendto(frame, (self._device_ip, int(self._send_port)))
            sock.close()
            self._session = (self._session + 1) & 0xFF
            self._last_action_time = asyncio.get_event_loop().time()
            if value and self._pulse_ms > 0:
                asyncio.get_event_loop().call_later(self._pulse_ms/1000.0, lambda: asyncio.create_task(self._send_command(0)))
        except Exception as e:
            _LOGGER.exception('Error sending binary command: %s', e)
