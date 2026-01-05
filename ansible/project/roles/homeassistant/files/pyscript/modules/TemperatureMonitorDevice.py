from basics import read_yaml_from_file
from notify import internal_managed_notification
from notify import managed_notification

import datetime
import homeassistant
import json
from enum import IntEnum
from decimal import Decimal 

THERMOMETERS_CONFIG_YAML_FILE="/config/pyscript/modules/thermometers.yaml"

class TemperatureMonitorDevice:
  
  def __init__(self, name):
    self.name = name   
    all_config = read_yaml_from_file(THERMOMETERS_CONFIG_YAML_FILE,  1024000)
    self.config = all_config[name]
    self.entity_name = (self.config)['name']
    log.info(self.name)
    log.info(self.entity_name)
    self.set_temp_state_name="input_number." + self.entity_name + "_set_temp"
    self.alerts_enabled_state_name="input_boolean." + self.entity_name + "_alerts_enabled"
    self.min_alert_value_state_name="input_number." + self.entity_name + "_min_alert_value"
    self.max_alert_value_state_name="input_number." + self.entity_name + "_max_alert_value"
    self.notification_id=self.entity_name + "_monitor_state"
    self.notification_title=title=self.entity_name.capitalize() + " Temperature Monitor"

  def get_state_value(self, state_name):
    return_value = 0;
    try: 
      return_value = state.get(state_name)
    except:
      default_tag = (state_name.split(".")[1]).replace(self.entity_name + "_","")
      return self.config['defaults'][default_tag]
    return return_value

  def get_current_state(self):
     return Decimal(state.get(self.name))

  def get_alert_enabled(self):
     return self.get_state_value(self.alerts_enabled_state_name)
  def get_set_temp(self):
     return self.get_state_value(self.set_temp_state_name)
  def get_min_alert_value(self):
     return Decimal(self.get_state_value(self.min_alert_value_state_name))
  def get_max_alert_value(self):
     return Decimal(self.get_state_value(self.max_alert_value_state_name))

  def monitor_alert(self, monitor_type):
    notify_config=self.config['renotify']
    # TODO:  Tnotify_config_interval could be missing...
    # also there's a bug lurking here in that the timer should be reset when the value gets back in range
    notify_config_interval=notify_config[monitor_type + "_INTERVAL"]
    renotify = True if notify_config_interval != -1 else False
    current_timestamp = datetime.datetime.now() 
    if "last_notified" in notify_config:
      log.debug("Last notified set... " + str(notify_config['last_notified']) + " with interval " + str(notify_config_interval) + " and current date time " + str(current_timestamp))
      time_diff = current_timestamp -  notify_config['last_notified']
      log.debug(time_diff.total_seconds()) 
      if time_diff.total_seconds() < notify_config_interval:
        renotify = False
    if renotify:
      message = self.name + " triggered alert for " +  monitor_type + ", min: " + str(self.get_min_alert_value()) + " ,max: " + str(self.get_max_alert_value()) + " ,current: " + str(self.get_current_state())
      managed_notification(notification_name=self.name, title=self.notification_title, message=message )
      notify_config['last_notified']=current_timestamp
    return renotify
     
  def process_monitor_type(self, monitor_type):
    log.info("Process monitor type: " + monitor_type + " for " + self.name + " current value " + str(self.get_current_state()))
    if monitor_type == "ABOVE_RANGE":
      if self.get_current_state() > self.get_max_alert_value():
        log.info(self.name + " is " + str(self.get_current_state()) + " which is above the desired range of " + str(self.get_min_alert_value()) + " and " + str(self.get_max_alert_value())) 
        self.monitor_alert(monitor_type)
    elif monitor_type == "BELOW_RANGE":
      if self.get_current_state() < self.get_min_alert_value():
        log.info(self.name + " is " + str(self.get_current_state()) + " which is below the desired range of " + str(self.get_min_alert_value()) + " and " + str(self.get_max_alert_value())) 
        self.monitor_alert(monitor_type)
    elif monitor_type == "INSIDE_RANGE":
      if self.get_current_state() < self.get_max_alert_value() and self.get_current_state() > self.get_min_alert_value():
        log.info(self.name + " is " + str(self.get_current_state()) + " which is within the desired range of " + str(self.get_min_alert_value()) + " and " + str(self.get_max_alert_value())) 
        self.monitor_alert(monitor_type)
    elif monitor_type == "SET_POINT":
      if self.get_current_state() ==  self.get_set_temp():
        log.info(self.name + " reached set temp " +  get_set_temp())
        self.monitor_alert(monitor_type)
    else:
      log.info("Invalid monitor type " + monitor_type + "  configured for " + self.name)
      #self.dump()

  def process_state_change(self):
    if self.get_alert_enabled() == "on":
      log.debug("Process called for " + self.name )
      monitor_types=self.config['monitor_types']
      for monitor_type in monitor_types:
        self.process_monitor_type(monitor_type)
    else:
      log.debug("Notifications disabled for " + self.name)

  def dump(self):
    details = {}
    details['name'] = self.name
    details['entity_name'] = self.entity_name
    details['current_state'] = str(self.get_current_state())
    details['alerts_enabled'] = str(self.get_alert_enabled())
    details['min_alert_value'] = str(self.get_min_alert_value())
    details['max_alert_value'] = str(self.get_max_alert_value())
    log.info(details)
    log.info(json.dumps(details, indent=4))
  
