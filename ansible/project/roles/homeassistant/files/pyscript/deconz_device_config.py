import calendar
from datetime import datetime, timedelta
from dateutil.tz import tzlocal
import homeassistant
import json
import requests
import re
import os

from DeconzDevice import DeconzDevice
from basics import write_json_file
from registry import devices
from registry import devicereg
from registry import entities
from registry import entityreg


deconz_devices = {}


def get_deconz_device(device_id):
  global deconz_devices
  deconz_device = None
  if device_id in deconz_devices:
    deconz_device = deconz_devices[device_id]
  if deconz_device == None:
    device_info = devices.get(device_id)
    deconz_device = DeconzDevice(device_info)
    deconz_devices[device_id] = deconz_device
  return deconz_device

@service
@time_trigger("cron(0 */6 * * *)")
@time_trigger("startup")
def load_deconz_devices():
  global deconz_devices
  for entity in entities:
    entity_info = entities.get(entity)
    if entity_info.platform == "deconz":
      device_info=devices.get(entity_info.device_id)
      deconz_device = get_deconz_device(device_info.id)
      deconz_device.add_entity(entity_info)


@service
def update_deconz_device_ids():
  for deconz_device in deconz_devices:
      log.info("")
      deconz_device = deconz_devices[deconz_device]
      for deconz_entity in deconz_device.entities:
        deconz_entity.update_entity_id()
      

