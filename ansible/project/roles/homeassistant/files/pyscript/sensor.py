from decimal import Decimal       
from packaging import version
from requests.structures import CaseInsensitiveDict

import json
import os                                                          
import re                                                          
import requests                                                         

from basics import read_json_from_file
from registry import devices
from registry import entities
from states import set_state

############################################################################
## STATE TRACKING TRIGGER FACTORY
############################################################################

def set_light_state_sensor(sensor_name):
  state_name=None
  state_value=0
  if sensor_name.endswith("brightness"):
    state_name="sensor.brightness_" + sensor_name.split(".")[1]
    try:
      state_value=state.get(sensor_name)
    except:
      pass
  else:
    state_name="sensor." + sensor_name.split(".")[1]
    value=state.get(sensor_name)
    if value == "on":
      state_value=1
    else:
      state_value=0
  if state_name != None:
    log.debug("set_light_state_sensor: " + state_name + " changed to " + str(state_value))
    set_state(state_name , str(state_value))

light_state_trigger_array = []
def light_state_trigger_factory(sensor_name):
  @state_trigger(sensor_name)
  def func_light_state_change(trigger_type=None, var_name=None, value=None):
    set_light_state_sensor(sensor_name)
  return func_light_state_change

light_state_periodic_array = []
def light_periodic_trigger_factory(sensor_name):
  @time_trigger("cron(*/10 * * * *)")
  def func_light_periodic_change():
    set_light_state_sensor(sensor_name)
  return func_light_periodic_change

dimmable_lights=""
switchable_lights=""
for entity in entities:
  if entity.startswith("light."):
    ent = entities.get(entity)
    device_id = ent.device_id
    dev = devices.get(device_id)
    if dev.model == "HS220(US)" or dev.model == "WLPA19" or dev.model == "LS5050C-TAS" or dev.model == "HL_HWB2":
      light_state_trigger_array.append(light_state_trigger_factory(ent.entity_id + ".brightness"))
      light_state_periodic_array.append(light_periodic_trigger_factory(ent.entity_id + ".brightness"))
    elif dev.model == "WLPP1" or dev.model == "HS200(US)" or dev.model == "Sonoff S31":
      light_state_trigger_array.append(light_state_trigger_factory(ent.entity_id))
      light_state_periodic_array.append(light_periodic_trigger_factory(ent.entity_id))
    else:
      log.debug(ent.entity_id)
      log.debug(dev.model)

#@service
#@time_trigger("cron(*/10 * * * *)")
#@time_trigger("startup")
#def get_db_file_info():
#  size_info_file=None
#  size_info_json=read_json_from_file("/config/db_size_info.json", 1024)
#
#  for entry in size_info_json:
#    name = entry['name']
#    size = entry['size']
#    size = Decimal(size)
#    size = round(size,2)
#    if not name.startswith("_"):
#      set_state("sensor." + name + "_db_size", size)

#@service
#@time_trigger("cron(*/10 * * * *)")
#@time_trigger("startup")
#def get_influx_dbpath_info():
#  size_info_file=None
#  size_info_json=read_json_from_file("/config/influx_db_size_info.json", 2048)
#  if size_info_json != None:
#    for entry in size_info_json:
#      name = entry['name']
#      size = entry['size']
#      size = Decimal(size)
#      size = round(size,2)
#      if name[0] == "_":
#        name = name[1:] 
#      set_state("sensor." + name + "_dbpath_size", size)
   


