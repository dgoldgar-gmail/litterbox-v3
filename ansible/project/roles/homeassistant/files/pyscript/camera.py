
from Camera import Camera

from notify import managed_notification
from registry import devices
from registry import entities

import json
import re 
import requests 

#################################################
# FRIGATE / OPENMIKO CAMERAS
################

cameras = {}

def get_camera(camera_device):
  global cameras
  name = camera_device.name.replace(" ","_").lower()
  camera = None
  if name in cameras:
    camera = cameras[name]
  if camera == None:
    camera = Camera(camera_device)
    cameras[name] = camera
  return camera

@service
@time_trigger("cron(0 */6 * * *)")
@time_trigger("startup")
def load_cameras():
  global cameras
  for dev in devices:
    dev_info=devices.get(dev)
    if "Frigate" == dev_info.manufacturer:
      log.info(dev_info.name)
    if "Frigate" == dev_info.manufacturer and dev_info.name.endswith("Camera"):
      camera = get_camera(dev_info)
      #camera.collect_version_info()


@service
def thingino_reboot(camera_name=None):
  camera = cameras[camera_name]
  camera.reboot()


@service
def thingino_info(data):
  global cameras
  for camera in cameras:
    if camera.replace("_camera","").replace("_","") == data['hostname'].replace("camera-",""):
      cc=cameras[camera]
      cc.update_thingino_info(data)
