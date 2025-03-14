"""Constants for the Caldera Spas integration."""

from datetime import timedelta

DOMAIN = "caldera"

# Config flow
CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# Default update interval
UPDATE_INTERVAL = timedelta(seconds=30)

# Services
SERVICE_SET_TEMPERATURE = "set_temperature"
SERVICE_SET_PUMP = "set_pump"
SERVICE_SET_LIGHTS = "set_lights"

# Attributes
ATTR_PUMP_SPEED = "pump_speed"
ATTR_PUMP_NUMBER = "pump_number"
ATTR_TEMPERATURE = "temperature"
