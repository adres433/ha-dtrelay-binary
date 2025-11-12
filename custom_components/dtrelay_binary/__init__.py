"""Dingtian Relay Binary integration - minimal __init__"""
from .const import DOMAIN
from homeassistant.core import HomeAssistant

async def async_setup_entry(hass: HomeAssistant, entry):
    # Placeholder for integration setup
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    return True
