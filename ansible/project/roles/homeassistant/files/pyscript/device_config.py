import calendar
from datetime import datetime, timedelta
from dateutil.tz import tzlocal
import homeassistant
import json
import requests
import re
import os

from basics import write_json_file
from registry import devices
from registry import devicereg
from registry import entities
from registry import entityreg
from tasmota import run_tasmota_command

json_file_name="/config/XXX/device_config.json"
aqara_device_list = {}
tasmota_device_list = {}
tplink_device_list = {}
wyze_device_list = {}

@service
def build_device_config():
  for entity in entities:
    ent=entityreg.async_get(entity)
    if ent.platform == "tplink":
      add_entity_to_list(ent,tplink_device_list,"TP-Link")
    elif ent.platform == "deconz":
      add_entity_to_list(ent,aqara_device_list,"LUMI")
    elif ent.platform == "tasmota":
      add_entity_to_list(ent,tasmota_device_list,"Tasmota")
    elif ent.platform == "wyzeapi":
      add_entity_to_list(ent,wyze_device_list,"WyzeLabs")
    else:
      #log.info(ent.platform)
      pass
  device_list = {}
  device_list['aqara'] = aqara_device_list
  device_list['tasmota'] = tasmota_device_list
  device_list['tplink'] = tplink_device_list
  #log.info(tplink_device_list)
  device_list['wyze'] = wyze_device_list

  write_json_file(json_file_name, device_list)

def add_entity_to_list(ent, device_list, mfgr):
  device_id=ent.device_id
  dev=devices.get(device_id)
  #log.info(dev)
  manufacturer = dev.manufacturer
  device_name = dev.name
  device_info={}
  if manufacturer == mfgr: 
    if device_id in device_list:
      device_info=device_list.get(device_id)
    else:
      device_info={}
      device_list[device_id] = device_info
      device_info['id']  = device_id
      device_info['name']  = device_name
      device_info['model']  = dev.model
      device_info['sw_version'] = dev.sw_version
      device_info['hw_version'] = dev.hw_version
      device_info['manufacturer'] = dev.manufacturer
      device_info['config_url'] = dev.configuration_url
      #device_info['new_id'] = get_new_device_id(mfgr,device_name,unique_id)
      device_info['new_name'] = get_new_device_name(mfgr,device_name)
      #update_device_name(device_id,device_info['new_name'])
      #log.info("Update device " + device_id + " to " + device_info['new_name'])
  
      entity_list = {}
      device_info['entities'] = entity_list
      if mfgr == "Tasmota": 
        try:
          add_tasmota_data_to_device(device_id, device_info)
        except:
          log.info("Failed getting tasmota info for device " + device_name)
           
    unique_id = ent.unique_id 
    entity_list = device_info['entities']
    entity_info = {}
    entity_list[unique_id] = entity_info
    entity_info['unique_id'] = unique_id
    entity_info['name'] = ent.name
    entity_info['id'] = ent.entity_id
    entity_info['id'] = ent.entity_id
    entity_info['new_id'] = get_new_entity_id(mfgr,device_info,entity_info)

    # Update entity_id or entity_name 
    if manufacturer == "LUMI":
      entity_info['new_name'] = get_new_entity_name(mfgr,device_name,unique_id)
      #update_entity_name(ent.entity_id,entity_info['new_name'])
      #try:
      #  update_entity_id(ent.entity_id,entity_info['new_id'])
      #except:
      #  pass
      log.info("Update name for LUMI entity " + ent.entity_id + " to " + entity_info['new_name'])
      log.info("Update id for LUMI entity " + ent.entity_id + " to " + entity_info['new_id'])
      pass
    if manufacturer == "WyzeLabs":
      entity_info['new_name'] = get_new_entity_name(mfgr,device_name,unique_id, dev.model)
      #log.info("Update  " + manufacturer + " name for entity " + str(entity_info['name']) + " to " + entity_info['new_name'])
      #log.info("Update  " + manufacturer + " id for entity " + str(entity_info['id']) + " to " + entity_info['new_id'])
      #update_entity_name(ent.entity_id,entity_info['new_name'])
    if manufacturer == "TP-Link":
      entity_info['new_name'] = get_new_entity_name(mfgr,device_name,unique_id)
      #update_entity_name(ent.entity_id,entity_info['new_name'])
    if mfgr == "Tasmota": 
      entity_info['new_name'] = get_new_entity_name(mfgr, device_name, unique_id, dev.model)
  return device_info


def add_tasmota_data_to_device(device_id, device_info):
  device_info.update(run_tasmota_command(device_id,"cm?cmnd=DeviceName"))
  device_info.update(run_tasmota_command(device_id,"cm?cmnd=FriendlyName1"))
  device_info.update(run_tasmota_command(device_id,"cm?cmnd=FriendlyName2"))
  device_info.update(run_tasmota_command(device_id,"cm?cmnd=Module"))
  device_info.update(run_tasmota_command(device_id,"cm?cmnd=PowerOnState"))
  wifi_data = {}
  device_info['WIFI'] = wifi_data
  wifi_data.update(run_tasmota_command(device_id,"cm?cmnd=Hostname"))
  wifi_data.update(run_tasmota_command(device_id,"cm?cmnd=SSId1"))
  wifi_data.update(run_tasmota_command(device_id,"cm?cmnd=SSId2"))
  #wifi_data.update(run_tasmota_command(device_id,"cm?cmnd=Password1"))
  #wifi_data.update(run_tasmota_command(device_id,"cm?cmnd=Password2"))
  wifi_data.update(run_tasmota_command(device_id,"cm?cmnd=IPAddress1"))
  mqtt_data = {}
  device_info['MQTT'] = mqtt_data
  mqtt_data.update(run_tasmota_command(device_id,"cm?cmnd=MqttHost"))
  mqtt_data.update(run_tasmota_command(device_id,"cm?cmnd=MqttUser"))
  #mqtt_data.update(run_tasmota_command(device_id,"cm?cmnd=MqttPassword"))
  mqtt_data.update(run_tasmota_command(device_id,"cm?cmnd=MqttClient"))


def get_entity_type(mfgr, entity_info):
  if mfgr == "Tasmota": 
    unique_id=entity_info['unique_id']
    unique_id_parts=unique_id.split("_")
    if unique_id_parts[1] == "status" and unique_id_parts[2] == "sensor":
      return "sensor"  
    elif unique_id_parts[1] == "sensor" and unique_id_parts[2] == "sensor":
      return "sensor"  
    elif unique_id_parts[1] == "switch" and unique_id_parts[2] == "relay":
      return "switch"  
    elif unique_id_parts[1] == "light" and unique_id_parts[2] == "light":
      return "light"  
    else:
      log("UNKNOWN_TYPE")
  elif mfgr == "LUMI":
    return entity_info['id'].split(".")[0]

def get_new_entity_id(mfgr, device, entity):
      device_name=device['name']
      unique_id=entity['unique_id']
      new_id=""
      if mfgr == "Tasmota":
        pattern = re.compile("([a-zA-Z0-9]*)_(.*)")
        uid_part=(pattern.match(unique_id))[2]
        uid_part = uid_part.replace("sensor_","")
        uid_part = (uid_part.replace("status_","")).lower()
        entity_type=get_entity_type(mfgr,entity)
        device_name_part = (((device_name.split(" "))[0]).lower()).replace("-","_")
        #log.info(device_name)
        new_id = entity_type + "." + device_name_part + "_" + uid_part
        #log.info(new_id)
        
      elif mfgr == "TP-Link":
        #log.info(device_name + " " + unique_id)
        pass
      elif mfgr == "LUMI":
        log.info(entity['name'])
        #new_id=("sensor." + entity['name']).lower().replace(" ","_").replace("'","_").replace("(","_").replace(")","_").replace("-","").replace("__","_").replace("__","_")
        #log.info(new_id) 
      return new_id

def get_new_entity_name(mfgr, device_name, unique_id, model=None):
  new_name=""
  if mfgr == "Tasmota":
    if "Sonoff S31" == model:
      new_name=device_name
      unique_id_splits = unique_id.split("_",1)
      unique_id_part=unique_id_splits[1]
      unique_id_part=unique_id_part.replace("status_","")
      unique_id_part=unique_id_part.replace("sensor_","")
      new_name=new_name + " " + unique_id_part
  elif mfgr == "TP-Link":
    new_name=device_name
    unique_id_splits = unique_id.split("_")
    if ( len(unique_id_splits) > 1 ):
      new_name = new_name + " - LED"
  elif mfgr == "LUMI":
    try: 
      name_split=device_name.split("-")
      id_split=unique_id.split("-")
      if len(id_split) == 4 :
        new_name=(name_split[0]).strip() + " (" + (name_split[1]).strip() + ") - " + (id_split[3]).capitalize()
      else:
        new_name=(name_split[0]).strip() + " (" + (name_split[1]).strip() + ")"
    except Exception as e:
      print(e)
      pass
  elif mfgr == "WyzeLabs":
    if "WYZEC1-JZ" == model:
      new_name = device_name + " - Camera"
    pass
  return new_name 

def get_new_device_name(mfgr, device_name):
  new_name=""
  if mfgr == "Tasmota":
    new_name = device_name
  elif mfgr == "TP-Link":
    device_name_splits=device_name.split(" ")
    for dns in device_name_splits:
      new_name = new_name + dns.capitalize() + " "
    new_name=new_name.strip()
    new_name=new_name.replace("’","")
  elif mfgr == "LUMI":
    new_name = device_name
  elif mfgr == "WyzeLabs":
    # Nothing to guess from.  
    new_name = device_name
  else:
    #log.info(dev)
    pass
  new_name=new_name.replace("’","")
  return new_name

def update_entity_id(id,new_id):
  entityreg.async_update_entity(entity_id=id, new_entity_id=new_id)

def update_entity_name(id,new_name):
  entityreg.async_update_entity(entity_id=id, name=new_name)

def update_device_name(id,new_name):
  devicereg.async_update_device(id, name=new_name)



