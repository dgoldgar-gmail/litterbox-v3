
import homeassistant

from basics import read_yaml_from_file

from enum import IntEnum
from homeassistant.const import EVENT_CALL_SERVICE
from registry import devices
from registry import entities
from states import set_state

# Gestures:
# 0 probably wake?  might be knock or double tap??
# 1 is shake
# 2 is drop
# 3 is flipped 90 degrees
#   1003 - First digit is to side,  last digit is from side. ( ie from 1 to 3)
#   3001 - First digit is to side,  last digit is from side. ( ie from 3 to 1)
# 4 flipped 180 degrees
# 5 slide
# 6 probably double tap?
# 7 rotate clockwise
# 8 rotate counter clockwise

GESTURE = IntEnum('Gesture', 'SHAKEN DROPPED FLIP_90 FLIP_180 SLID DOUBLE_TAPPED ROTATED_CLOCKWISE ROTATED_COUNTER_CLOCKWISE')
CUBES_YAML_FILE="/config/pyscript/modules/cubes.yaml"


class Cube:
  config_yaml = read_yaml_from_file(CUBES_YAML_FILE,  102400)
  def __init__(self, device_obj):
    self.name = device_obj.name
    log.debug(">>  Setting up " + self.name)
    self.location = device_obj.area_id
    self.cube_config = Cube.config_yaml[self.location]
    self.side_up = 1
    self.gestures = {}
    self.gestures[GESTURE.SHAKEN.name] = Gesture(self, GESTURE.SHAKEN.name)
    self.gestures[GESTURE.DROPPED.name] = Gesture(self, GESTURE.DROPPED.name )
    self.gestures[GESTURE.DOUBLE_TAPPED.name] = Gesture(self, GESTURE.DOUBLE_TAPPED.name)
    self.gestures[GESTURE.SLID.name] = Gesture(self, GESTURE.SLID.name, False)
    self.gestures[GESTURE.ROTATED_CLOCKWISE.name] = Gesture(self, GESTURE.ROTATED_CLOCKWISE.name, False)
    self.gestures[GESTURE.ROTATED_COUNTER_CLOCKWISE.name] = Gesture(self, GESTURE.ROTATED_COUNTER_CLOCKWISE.name, False)
    self.group_entity_associations = {}
    for association_name in self.cube_config['group_entity_assocations']:
      entities = self.cube_config['group_entity_assocations'][association_name]
      association = GroupEntityAssociation(association_name, entities)
      self.group_entity_associations[association_name]  = association

  def process_event(self, event, id, unique_id, gesture):
    log.info("Processing cube event: " + str(event) + " " + str(id) + " " + str(unique_id) + " " + str(gesture))
    if gesture == GESTURE.FLIP_90 or gesture == GESTURE.FLIP_180:
      self.side_up = str(event)[0]
      log.debug("side_up set to " + self.side_up)
    elif gesture != 0:
      log.debug((GESTURE(gesture)).name)
      gesture = self.gestures[(GESTURE(gesture)).name]
      for action in gesture.actions:
        action.process_event(self.side_up)

  def dump(self): 
    log.info(self.name) 
    log.info("\tlocation: " + self.location) 
    log.info("\tside_up: " + str(self.side_up))
    log.info("\tgestures:")
    for gesture in self.gestures:
      self.gestures[gesture].dump()

class Gesture:
  def __init__(self, cube, name, simple=True):
    log.debug(">> Setting up gesture " + name)
    self.cube = cube
    self.name = name
    self.simple = simple
    self.actions = []
    if name in cube.cube_config['gestures']:
      if simple:
        for group_name in cube.cube_config['gestures'][name]:
          action_name = cube.cube_config['gestures'][name][group_name]
          action = Action(cube, self.name, group_name, action_name)
          self.actions.append(action)
      else:
        for side_group_name in cube.cube_config['gestures'][name]:
          side_group_actions = cube.cube_config['gestures'][name][side_group_name]
          for side in cube.cube_config['side_action_map']:
            group_for_side = str(cube.cube_config['side_action_map'][side])
            if side_group_name == group_for_side:
              for action_group_name in side_group_actions:
                action = Action(cube, self.name, action_group_name, side_group_actions[action_group_name], str(side))
                self.actions.append(action)

  def dump(self):
    log.info("\t\tname:" + self.name)
    log.info("\t\tsimple: " + str(self.simple))
    for action in self.actions:
      action.dump();

class Action:
  def __init__(self, cube, gesture_name,  action_groupname, name, side_association=None ):
    self.cube = cube
    self.name = name   
    self.gesture_name = gesture_name
    self.group_name = action_groupname
    self.side_association = side_association

  def dump(self):
    log.info("\t\t\t(" + self.cube.name + "::" + self.gesture_name + ") => " + self.group_name + " => "  + self.name + "(" + self.side_association  + ")")

  def process_event(self, side):
    if self.side_association is None or self.side_association == str(side):
        for entity in self.cube.group_entity_associations[self.group_name].entities:
          log.info("Process " + self.name + " for " + entity )
          if self.name == "turn_off_lights":
            self.turn_off_lights(entity)
          elif self.name == "turn_on_lights":
            self.turn_on_lights(entity)
          elif self.name == "increase_brightness":
            self.adjust_brightness(entity,True)
          elif self.name == "decrease_brightness":
            self.adjust_brightness(entity,False)
          elif self.name == "increase_rgb_color":
            self.adjust_rgb_color(entity, self.side_association, increase=True)
          elif self.name == "decrease_rgb_color":
            self.adjust_rgb_color(entity, self.side_association, increase=False)

  def turn_off_lights(self, entity):
    light.turn_off(entity_id=entity)

  def turn_on_lights(self, entity):
    light.turn_on(entity_id=entity, brightness=255)

  def adjust_brightness(self, entity, increase=True):
    set_value=self.get_set_value(entity, increase)
    light.turn_on(entity_id=entity, brightness=set_value)

  # This might not be as nice as it was before, the values won't immediately snap to a level...
  # could be fixed by calling it on a group of entities or something
  def get_set_value(self, entity, increase=True):
    new_value=state.get(entity + ".brightness")
    if new_value == None:
      return 255
    elif increase == True:
      return min(new_value+20,255)
    else:
      return max(new_value-20,10)

  def adjust_rgb_color(self, entity, side_up, increase=True):
    log.info("adjust_rgb_color: " + str(entity))
    try:
      set_values = state.get(entity + ".rgb_color")
    except:
      set_values = [0,0,0]

    set_list = list(set_values)
    log.debug(set_list)
    chg_value = set_list[int(side_up) - 3]
    if increase:
      chg_value = min(chg_value+20, 255)
    else:
      chg_value = max(chg_value-20, 0)
    set_list[int(side_up) - 3] = chg_value
    set_values=tuple(set_list)
    log.info(entity + " " + str(set_list))
    light.turn_on(entity_id=entity, rgb_color=set_list)

class GroupEntityAssociation:
  def __init__(self, group_name, entities):
    self.group_name = group_name
    self.entities = entities

  def dump(self):
    log.info("\t\t\t" + group_name + " => " + str(entities)) 





