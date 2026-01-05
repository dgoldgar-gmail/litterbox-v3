from notify import managed_notification
from basics import read_json_from_file

from registry import devices
from registry import entities

from homeassistant.const import EVENT_STATE_CHANGED

from Camera import Camera
from Button import Button
from Cube import Cube

from registry import devices

@service
def delete_state():
  state.delete("sensor.motion_sensor_main_hall_temperature")
  state.delete("sensor.motion_sensor_family_room_temperature")
  state.delete("sensor.motion_sensor_cat_box_temperature")
  state.delete("sensor.motion_sensor_basement_temperature")



#@service
#def process_lumis():
#  for device_id in devices:
#    device_obj=devices.get(device_id)
#    if device_obj.model == "lumi.remote.b1acn01":
#      button = Button(device_obj)
#      button.dump()
#    if device_obj.model == "lumi.sensor_cube.aqgl01":
#      #log.info("cube=>" + str(device_obj.name))
#      x = Cube(device_obj) 
#      #x.dump()

