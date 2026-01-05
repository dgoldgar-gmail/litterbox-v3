import calendar
from datetime import datetime, timedelta
from dateutil.tz import tzlocal
import homeassistant
import json
import requests
import re
import os

from TasmotaDevice import TasmotaDevice
from basics import write_json_file
from registry import devices
from registry import devicereg
from registry import entities
from registry import entityreg


tasmota_devices = {}


def get_tasmota_device(device_id):
  global tasmota_devices
  tasmo_device = None
  if device_id in tasmota_devices:
    tasmo_device = tasmota_devices[device_id]
  if tasmo_device == None:
    device_info = devices.get(device_id)
    tasmo_device = TasmotaDevice(device_info)
    tasmota_devices[device_id] = tasmo_device
  return tasmo_device

@service
@time_trigger("cron(0 */6 * * *)")
@time_trigger("startup")
def load_tasmota_devices():
  global tasmota_devices
  for entity in entities:
    entity_info = entities.get(entity)
    if entity_info.platform == "tasmota":
      device_info=devices.get(entity_info.device_id)
      tasmo_device = get_tasmota_device(device_info.id)
      tasmo_device.add_entity(entity_info)
  for tasmo_device in tasmota_devices:
    td = tasmota_devices[tasmo_device]
    #td.dump()


@service
def update_tasmota_device_ids():
  for tasmo_device in tasmota_devices:
      log.info("")
      tasmo_device = tasmota_devices[tasmo_device]
      for tasmo_entity in tasmo_device.entities:
        tasmo_entity.update_entity_id()



