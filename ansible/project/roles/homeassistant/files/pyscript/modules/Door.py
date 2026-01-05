
from states import get_state
from notify import managed_notification
from registry import entities

import datetime
import asyncio

CHECK_INTERVAL=60

class Door:
  def __init__(self, entity_obj):
    self.entity = entity_obj
    self.name = entity_obj.entity_id
    self.short_name = self.name.replace("binary_sensor.door_sensor_","").replace("_open","") + "_door"
    self.friendly_name = self.short_name.replace("_", " " ).title()
    self.door_state = state.get(self.name)
    self.state_change_timestamp = datetime.datetime.now() 
    self.previous_state = "None"
    self.dump()


  def dump(self):
    log.info("Door:: " + self.name)
    log.info("\tshort_name: " + self.short_name)
    log.info("\t" + self.door_state + " since " + str(self.state_change_timestamp))

  def process_state(self, door_state):
    previous_state = self.door_state
    self.door_state = "Closed" if door_state == "off" else "Open"
    log.info("Processing door state for door " + self.short_name + " changed from  " + self.previous_state + " to " + self.door_state)
    if self.door_state == "Open":
      self.notify(self.short_name + "_open_close", initial=True)
      while True:
        asyncio.sleep(CHECK_INTERVAL)
        self.notify(self.short_name + "_left_open", initial=False)
        log.debug(self.door_state)
        if self.door_state == "Closed":
          log.info("Door left open event over!")
          break;

  def notify(self, note_name,  initial=True):
    if self.door_state == "Open":    
      if initial == True:
        message="The door - " + self.friendly_name + " - was opened."
        title=self.friendly_name + " Opened"
      else:
        message="The door - " + self.friendly_name + " - has been open since " + str(self.state_change_timestamp)
        title=self.friendly_name + " Left Open!"
    else:
      message="The door - " + self.friendly_name + " - was closed."
      title=self.friendly_name + " Closed"
    log.info(message)
    managed_notification(notification_name=note_name, title=title, message=message)
      




