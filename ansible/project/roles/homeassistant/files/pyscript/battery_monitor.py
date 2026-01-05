from notify import managed_notification

from registry import devices
from registry import entities

from homeassistant.const import EVENT_STATE_CHANGED

@event_trigger(EVENT_STATE_CHANGED)
def monitor_state_change(entity_id=None, new_state=None, old_state=None):
    if entity_id.startswith("sensor.thermometer") or entity_id.startswith("sensor.door") or entity_id.startswith("sensor.magic_cube") or entity_id.startswith("sensor.motion") or entity_id.startswith("sensor.switch") or entity_id.startswith("sensor.meatometer_"):
      if "battery" in entity_id:
        name = ""
        if entity_id.startswith("sensor.meatometer_"):
          name = entity_id.replace("sensor.", "")
        else: 
          ent=entities.get(entity_id)
          name = str(ent.name)
        title="Low Battery ( " + name + ")"
        try:
          if int(new_state.state) > 25:
            persistent_notification.dismiss(notification_id=title)
          else:
            managed_notification(notification_name=entity_id.replace("sensor.",""), title=title, message=title)
        except:
          pass
         
 
