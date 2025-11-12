"""Minimal switch platform for Dingtian Relay Binary"""
from homeassistant.components.switch import SwitchEntity

class DTRelaySwitch(SwitchEntity):
    def __init__(self, name):
        self._name = name
        self._is_on = False

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        self._is_on = True

    async def async_turn_off(self, **kwargs):
        self._is_on = False
