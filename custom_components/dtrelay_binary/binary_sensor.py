from homeassistant.components.binary_sensor import BinarySensorEntity
from .const import MAX_CHANNELS
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    entry_id = entry.entry_id
    sensors = [DTRelayInput(hass, entry_id, i) for i in range(MAX_CHANNELS)]
    async_add_entities(sensors, True)

class DTRelayInput(BinarySensorEntity):
    def __init__(self, hass, entry_id, index):
        self._hass = hass
        self._entry_id = entry_id
        self._index = index
        self._attr_name = f"{entry.data.get('name')}_{entry.data.get('sn')}_in{index+1}"
        self._attr_unique_id = f"{entry_id}_in_{index+1}"
        self._state = False
        hass.bus.async_listen('dtrelay_frame_received', self._update)

    def _update(self, event):
        if event.data.get('entry_id') != self._entry_id:
            return
        inputs = event.data.get('inputs')
        if inputs and len(inputs) > self._index:
            new = inputs[self._index]
            if new != self._state:
                self._state = new
                self.schedule_update_ha_state()

    @property
    def is_on(self):
        return self._state
