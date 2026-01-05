from Button import Button
from Cube import Cube
from Door import Door
from registry import devices
from registry import entities
from homeassistant.const import EVENT_STATE_CHANGED

##########################
## Globals
#########

buttons = {}
cubes = {}
doors = {}

#################################################
# DECONZ EVENT HANDLER SERVICE:
################
@event_trigger("deconz_event")
def process_deconz_event(device_id, event, id, unique_id, gesture=None):
  global buttons
  log.info("process deconz event")
  device=devices.get(device_id)
  if device.model == "lumi.remote.b1acn01":
    button = buttons[device.area_id]
    button.process_event(event, id, unique_id)
  elif device.model == "lumi.sensor_cube.aqgl01":
    cube = cubes[device.area_id]
    cube.process_event(event, id, unique_id, gesture)
  else:
    door = doors[device.area_id]
    door.process_event(event)

#################################################
# DECONZ SENSOR STATE CHANGE HANDLER SERVICES:
################
def door_sensor_state_change(sensor_name):
  state_name=None
  state_value=0
  current_state=state.get(sensor_name)
  log.info(sensor_name + " set to " + current_state)
  log.info("Doors: " + str(doors))
  door=doors.get(sensor_name)
  #log.info("Door: " + str(door))
  door.process_state(current_state)
  # TODO:  Something useful?

    
door_sensor_state_trigger_array = []
def door_sensor_state_trigger_factory(sensor_name):
  @state_trigger(sensor_name)
  def func_door_sensor_state_change(trigger_type=None, var_name=None, value=None):
    door_sensor_state_change(sensor_name)
  return func_door_sensor_state_change

door_sensor_state_func_array=[]
for entity in entities:
  if entity.startswith("binary_sensor.door"):
    ent = entities.get(entity)
    device_id = ent.device_id
    dev = devices.get(device_id)
    door_sensor_state_func_array.append(door_sensor_state_trigger_factory(ent.entity_id))


##################################################
# CREATE BUTTON AND CUBE OBJECTS FOR LUMI/DECONZ BUTTONS
################


def get_button(button_device):
  global buttons
  name = button_device.area_id
  button = None
  if name in buttons:
    button = buttons[name]
  if button == None:
    button = Button(button_device)
    buttons[name] = button
  return button

def get_cube(cube_device):
  global cubes
  name = cube_device.area_id
  cube = None
  if name in cubes:
    cube = cubes[name]
  if cube == None:
    cube = Cube(cube_device)
    cubes[name] = cube
  return cube

def get_door(door_entity):
  global doors
  name = door_entity.entity_id
  door = None
  if name in doors:
    door = doors[name]
  if door == None:
    door = Door(door_entity)
    doors[name] = door
  return door

@service
@time_trigger("cron(0 */6 * * *)")
@time_trigger("startup")
def load_lumi_devices():
  for dev in devices:
    dev_info=devices.get(dev)
    if dev_info.model == "lumi.remote.b1acn01":
      try:
        button = get_button(dev_info)
      except:
        log.debug("Button missing configuration: " + dev_info.area_id)
    elif dev_info.model == "lumi.sensor_cube.aqgl01":
      try:
        cube = get_cube(dev_info)
      except Exception as e:
        log.info("Failed initializing a cube " + str(dev_info))


@service
@time_trigger("cron(0 */6 * * *)")
@time_trigger("startup")
def load_lumi_entities():
  for entity_id in entities:
    entity_obj = entities.get(entity_id)
    if entity_obj.platform == "deconz" and entity_obj.original_device_class == "opening":
      door = get_door(entity_obj)
      #door.dump()



