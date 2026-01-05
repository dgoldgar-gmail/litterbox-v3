import calendar
import homeassistant
import json
import re
import requests
import os

from datetime import datetime, timedelta
from dateutil.tz import tzlocal
from string import capwords

from basics import read_json_from_file
from registry import devices
from registry import entities
from registry import update_entity_id
from registry import update_entity_name
from registry import update_device_name
from tasmota import run_tasmota_command

@time_trigger("cron(0 0 1 * *)")
@service 
def reset_tasmota_energy_total():
  for dev in devices:
    try: 
      run_tasmota_command(dev,"cm?cmnd=EnergyTotal%200","Sonoff S31")
    except: 
      device=devices.get(dev)
      log.info("Unable to reset energy total for " + device.name)

@service 
def set_tasmota_timezone():
  for dev in devices:   
    run_tasmota_command(dev,"cm?cmnd=timezone%20-4")

@service
def get_tasmota_timezone():      
  for dev in devices:
    run_tasmota_command(dev,"cm?cmnd=timezone")

@service
def check_timezone():
  localtimezone = tzlocal()
  log.info(localtimezone)
  log.info(datetime.now(tzlocal()))

@service 
def upgrade_tasmota_device(entity=None):
  log.info(entity)
  entity_obj = entities.get(entity)
  device_id=entity_obj.device_id
  device = devices.get(device_id)
  log.info("Upgrade tasmota device: " + device.name)
  run_tasmota_command(device_id,"cm?cmnd=Upgrade%201")


canary_group = ["06"]
stagger_group = ["03","10"]

@service
def tasmota_upgrade(type="canary"):
  group = ["01","02","03","04","05","01","07","08","09","10"]
  if type == "canary":
    group = canary_group
  elif type == "stagger":
    group = stagger_group
  for id in group:
    upgrade_tasmota_device("switch.tasmota_" + id)
    upgrade_tasmota_device("sensor.tasmota_rgb_game_room_firmware_version")
    upgrade_tasmota_device("sensor.tasmota_rgb_sams_room_firmware_version")

@service   
def set_tasmota_device_attribute(entity=None, attribute=None, value=None):
  log.info(entity)
  log.info(attribute)
  log.info(value)
  entity=entities.get(entity)
  device_id=entity.device_id
  device = devices.get(device_id)
  cmd_string=("cm?cmnd=" + attribute + "%20" + value)
  log.info("For device: " + device.name + " run_command " + cmd_string)
  run_tasmota_command(device_id,cmd_string)

@service
def set_blerry_version():
  for entity in entities:
    entity_obj = entities.get(entity)
    if entity_obj.platform == "tasmota":
      cmd_string="bc?c2=0&c1=print(blerry_version)"
      device_obj = devices.get(entity_obj.device_id)
      if device_obj.model == "ESP32-DevKit":
        configuration_url=device_obj.configuration_url
        configuration_url=configuration_url + cmd_string
        resp = task.executor(requests.get, configuration_url )
        data=resp.content
        data=data.decode("utf-8")
        data=data.split(")")[1]
        log.info(entity)
        parts = entity.split("_")
        state_name=parts[0] + "_" + parts[1] + "_" + parts[2] + "_blerry_version"
        log.info(state_name + " => " + data) 
        state.set(state_name, data)
        break
  

@service
@time_trigger("cron(0 * * * *)")
def update_tasmota_device_input_list():
  options=[]
  for entity in entities:
    if entity.startswith("switch.tasmota"):
      options.append(entity)
  options.sort()
  input_select.set_options(entity_id="input_select.selected_tasmota_device",options=options)

#@service
#def do_dumb_tasmota_stuff():
#  for dev in devices:
#    device = devices.get(dev)
#    if device.manufacturer == 'Tasmota':
#      if device.model == 'ESP32-DevKit':
#        #log.info(device)
#        log.info(run_tasmota_command(dev,"cm?cmnd=status%204"))
#        #log.info(run_tasmota_command(dev,"cm?cmnd=BLEDevices"))

@service
def apply_tasmota_device_harness(update_device_names=False, update_entity_names=False, update_entity_ids=False, models=['Sonoff S31','LB01-15W-RGBCCT-TAS','Arilux LC11','MagicHome','ESP32-DevKit']):
  mapping=read_json_from_file("/config/XXX/tasmota_mapping.json", 102400) 
  #log.info(mapping)
  devices_map = {}
  for entityname in entities:
    entity_obj=entities.get(entityname)
    device_id=entity_obj.device_id
    device = devices.get(device_id)
    device_name = None
    device_description = None
    if device != None and device.manufacturer == "Tasmota":
      device_ip=device.configuration_url.split("/")[2]
      if device.model not in models:
        continue
      device_id=device.id
      for inst in mapping['devices']:
        if inst['ip']  == device_ip:
          device_description = inst['description']
          device_full_name = inst['full_name']
          device_name = inst['name']
          break;
      if device_id not in devices_map:
        device_full_name = str(device_name) + " (" + str(device_description) + ")"
        devices_map[device_id] = {}
        devices_map[device_id]['name'] = device_full_name
        devices_map[device_id]['entities'] = []
      tentities = devices_map[device_id]['entities']
      
      pattern = re.compile("([a-zA-Z0-9]*)_(.*)")
      type_part=(pattern.match(entity_obj.unique_id))[2]
      type_part = type_part.replace("sensor_","")
      type_part = (type_part.replace("status_","")).lower()
      entity_type = (entity_obj.entity_id).split(".")[0]
      new_id = entity_type + "." +  str(device_name) + "_" + type_part
      entity_map = {}
      entity_map['old_id'] = entity_obj.entity_id
      entity_map['new_id'] = new_id
      entity_map['new_name'] = capwords(type_part.replace("_", " "))
      tentities.append(entity_map)
  log.debug(json.dumps(devices_map,indent=2))

  for device_id in devices_map:
    device_obj = devices_map[device_id]
    new_name = device_obj['name']
    if  update_device_names:
      try:
        update_device_name(id,new_name)
      except:
        log.info("Failed to update device name " + device_id + "=>" + new_name)
    for entity in device_obj['entities']:
      old_entity_id=entity['old_id']
      new_entity_id=entity['new_id']
      new_entity_name=entity['new_name']

      if update_entity_names:
        try:
          log.debug("Updating entity name for " + old_entity_id + " to " + new_entity_name)
          update_entity_name(old_entity_id,new_entity_name)
        except:
          log.info("Failed to update entity name for " + old_entity_id + " to " + new_entity_name)

      if update_entity_ids:
        try:
          log.debug("Updating entity id for " + old_entity_id + " to " + new_entity_id)
          update_entity_id(old_entity_id, new_entity_id)
        except:
          log.info("Failed to update entity id for " + old_entity_id + " to " + new_entity_id)



