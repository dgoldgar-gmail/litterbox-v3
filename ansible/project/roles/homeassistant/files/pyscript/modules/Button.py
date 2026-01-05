from basics import read_yaml_from_file
from registry import devices

import time

from enum import IntEnum

# 1001 - long press - hold?
# 1002 - single click
# 1003 - long press - release?
# 1004 - double click

GESTURE = IntEnum('Event', 'LONG_PRESS_HOLD SINGLE_CLICK LONG_PRESS_RELEASE DOUBLE_CLICK')
BUTTONS_YAML_FILE="/config/pyscript/modules/buttons.yaml"

class Button:
  config_yaml = None
  def __init__(self, device_obj):
    if Button.config_yaml == None:
      Button.config_yaml =read_yaml_from_file(BUTTONS_YAML_FILE,  102400)    
    self.device_name = device_obj.name
    self.location = device_obj.area_id
    self.gestures = {}
    self.gestures[GESTURE.LONG_PRESS_HOLD.name] = Gesture(self, GESTURE.LONG_PRESS_HOLD.name)
    self.gestures[GESTURE.SINGLE_CLICK.name] = Gesture(self, GESTURE.SINGLE_CLICK.name)
    self.gestures[GESTURE.LONG_PRESS_RELEASE.name] = Gesture(self, GESTURE.LONG_PRESS_RELEASE.name)
    self.gestures[GESTURE.DOUBLE_CLICK.name] = Gesture(self, GESTURE.DOUBLE_CLICK.name)
    self.LONG_PRESS_ACTIVE = False
    self.LONG_PRESS_BUTTON_SETTING = "increase"
    
  def dump(self):
    log.info(self.device_name)
    log.info("\t\tLONG_PRESS_ACTIVE=>" + str(self.button.LONG_PRESS_ACTIVE))
    log.info("\t\tLONG_PRESS_BUTTON_SETTING=>" + self.button.LONG_PRESS_BUTTON_SETTING)
    for gesture in self.gestures:
      self.gestures[gesture].dump()

  def process_event(self, event, id, unique_id):
    gesture = int(str(event)[3])
    gesture_name = (GESTURE(gesture)).name
    gesture = self.gestures[gesture_name]
    gesture.execute()


class Gesture:
  def __init__(self, parent, name):
    self.name = name
    self.groups = []
    self.button = parent
    groups = Button.config_yaml[parent.location]['group_action_map'][name]
    for group_name in groups.keys():
      action = Button.config_yaml[parent.location]['group_action_map'][name][group_name]
      entities = Button.config_yaml[parent.location]['gesture_group_map'][group_name]
      group = GroupAction(self.button, group_name, action, entities)
      self.groups.append(group)

  def dump(self):
    log.info("\t" + self.name)
    for group in self.groups:
      group.dump()

  def execute(self):
    for group in self.groups:
      group.execute()


class GroupAction:
  def __init__(self, button, name, action, entities):
    self.name = name
    self.action = action
    self.entities = entities
    self.button = button

  def dump(self):
    log.info("\t\t" + self.name + "=>" + self.action + "(" + str(self.entities) + ")")

  def execute(self):
    log.debug("Execute " + self.action)
    if self.action == "toggle_lights":
      self.toggle_lights(self.entities)
    elif self.action == "toggle_increase_decrease_brightness":
      self.button.LONG_PRESS_BUTTON_SETTING = "increase" if self.button.LONG_PRESS_BUTTON_SETTING == "decrease" else "decrease"
      log.debug("Set LONG_PRESS_BUTTON_SETTING to " + self.button.LONG_PRESS_BUTTON_SETTING)
    elif self.action == "stop_adjust_brightness":
      log.info("Set LONG_PRESS_ACTIVE False")
      self.dump()
      self.button.LONG_PRESS_ACTIVE=False
    elif self.action == "start_adjust_brightness":
      log.info("Set LONG_PRESS_ACTIVE True and start increasing brightness.")
      self.start_adjust_brightness(self.entities)

  def toggle_lights(self, target_entities):
      for target_entity in target_entities:
        current_state = state.get(target_entity)
        if current_state == "on":
          log.debug("Change state of " + target_entity + " from " + str(current_state) + " to off")
          light.turn_off(entity_id=target_entity)
        else:
          log.debug("Change state of " + target_entity + " from " + str(current_state) + " to on")
          light.turn_on(entity_id=target_entity)
    
  def start_adjust_brightness(self, target_entities):
    log.info("start_adjust_brightness")
    self.button.LONG_PRESS_ACTIVE=True
    for x in range(1, 50):
      self.dump()
      if self.button.LONG_PRESS_ACTIVE == False:
        break;
      for target_entity in target_entities:
        current_brightness=int(state.get(target_entity + ".brightness"))
        current_brightness = 0 if current_brightness == None else current_brightness
        if self.button.LONG_PRESS_BUTTON_SETTING == "increase":
          if current_brightness < 255:
            current_brightness = current_brightness + 20
          else:
            self.button.LONG_PRESS_ACTIVE = False
            break
        else:
          if current_brightness > 30:
            current_brightness = current_brightness - 20
          else:
            self.button.LONG_PRESS_ACTIVE = False
            break
        light.turn_on(entity_id=target_entity, brightness=current_brightness)
      time.sleep(1)
  
