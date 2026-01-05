
import requests

from registry import devices
from registry import entities

def run_tasmota_command(device_id,cmd,model=None):
  device=devices.get(device_id)
  if device.manufacturer == 'Tasmota':
    if model != None and device.model != model:
      log.info("Skipping device due to type mismatch")
    else:
      configuration_url=device.configuration_url
      configuration_url=configuration_url+cmd
      #log.info(configuration_url)
      resp = task.executor(requests.get, configuration_url )
      data = resp.json()
      return data


