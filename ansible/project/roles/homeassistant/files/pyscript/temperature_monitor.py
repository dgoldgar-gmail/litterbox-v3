from TemperatureMonitorDevice import TemperatureMonitorDevice
from basics import read_yaml_from_file
from registry import devices
from registry import entities

import datetime
import homeassistant
import json
from enum import IntEnum
from decimal import Decimal 

THERMOMETERS_CONFIG_YAML_FILE="/config/pyscript/modules/thermometers.yaml"

monitored_temperature_devices = {}

######################################################################
## Services...
################# 

@service
def set_temp_monitor_state(monitor_entity=None, monitor_value=None):
  if monitor_entity == "grilldome" or monitor_entity == "grillmeat" or monitor_entity == "woodstove":
    sensor_name="input_boolean." + monitor_entity + "_alerts_enabled"
    if monitor_value == "on" or monitor_value == "off": 
      try:
        state.set(sensor_name, monitor_value)
      except:
        state.set(sensor_name,get_temp_monitor_default_state(monitor_entity))
    else:
      try:
        ent_state=state.get(sensor_name)
        if ent_state == "on":
          ent_state=state.set(sensor_name, "off")
        else:
          ent_state=state.set(sensor_name, "on")
      except:
        log.debug("Error setting")
        state.set(sensor_name,get_temp_monitor_default_state(monitor_entity))
  else:
    log.debug("Invalid monitor_entity " + str(monitor_entity))
    
@service
@state_trigger("sensor.woodstove_temperature_gv, sensor.grilldome_temp_gv, sensor.grillmeat_temp_gv")
def temperature_range_monitor(trigger_type=None, var_name=None, value=None):
  global monitored_temperature_devices
  if var_name in monitored_temperature_devices:
    tdevice = monitored_temperature_devices[var_name]
  else: 
    log.info("Creating new monitored_temperature_device " + var_name)
    tdevice=TemperatureMonitorDevice(var_name)
    monitored_temperature_devices[var_name] = tdevice
  tdevice.process_state_change()


#@service
#def configure_battery_monitors():
#  for entity in entities:
#    entity_obj = entities.get(entity)
#    if entity_obj.original_device_class == "battery":
#        device_obj = devices.get(entity_obj.device_id)
#        if device_obj.model == "lumi.weather":
#          log.info(entity)
#
