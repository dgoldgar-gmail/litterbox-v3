from commands import execute_command_over_ssh
from datetime import datetime
from notify import managed_notification

import requests

class Camera:

  EXTERNAL_FRIGATE_API_URL="https://frigate.authabitrail.duckdns.org/api"
  INTERNAL_FRIGATE_API_URL="http://192.168.50.11:5000/api"

  def __init__(self, device_obj):
    self.device_name = device_obj.name
    log.info("Building Camera Object for " + self.device_name)
    self.name = self.device_name.replace(" ","_").lower()
    self.location_name = self.name.replace("_camera","")
    self.ip=""
    self.factory_methods = []
    self.factory_methods.append(self.object_sensor_state_trigger_factory(self.location_name, "cat"))
    self.factory_methods.append(self.object_sensor_state_trigger_factory(self.location_name, "car"))
    self.factory_methods.append(self.object_sensor_state_trigger_factory(self.location_name, "person"))

  def dump(self):
    log.info(self.device_name)
    log.info("\t" + self.name)
    log.info("\t" + self.location_name)
    log.info("\t" + self.ip)
    log.info("\t" + self.version)
    log.info("\t" + self.uptime)
    log.info("\t" + self.last_updated)
    log.info("\t" + self.blue_led)
    log.info("\t" + self.yellow_led)

  #################
  ## Frigate
  #####

  def object_sensor_state_trigger_factory(self, location_name, occupancy_type):
   sensor_name = "binary_sensor." + location_name + "_camera_" + occupancy_type + "_occupancy"
   log.debug("Build state trigger for " + sensor_name)
   @state_trigger(sensor_name)
   def func_object_sensor_state_change():
     current_state=state.get(sensor_name)

     if current_state == "off":
       log.debug(sensor_name + " state changed to off")
     else:
       log.debug(sensor_name + " state changed to on")
       title = None
       message = None
       if occupancy_type == "car" and state.get("input_boolean.global_car_detection_notifications") == "on":
         title = "Car Detected"
         message = "Car detected in " + location_name
       if occupancy_type == "cat" and state.get("input_boolean.global_cat_detection_notifications") == "on":
         title = "Cat Detected"
         message = "Cat detected in " + location_name
       if occupancy_type == "person" and state.get("input_boolean.global_person_detection_notifications") == "on":
         title = "Person Detected"
         message = "Person detected in " + location_name
       if title != None and message != None:
         title = title + " - " + location_name
         self.send_notification(title, message)
   return func_object_sensor_state_change
  
  def resolve_ip(self, camera):
    config_url= Camera.INTERNAL_FRIGATE_API_URL + "/config"
    resp = task.executor(requests.get, config_url )
    data=resp.json()
    rtsp_url=data['go2rtc']['streams'][camera][0]
    ip=(rtsp_url.split("/")[2]).split(":")[0]
    return ip

  def get_inprogress_event_id(self):
    api_url = Camera.INTERNAL_FRIGATE_API_URL + "/events?camera=" + self.location_name + "_camera&in_progress=1"
    resp = task.executor(requests.get, api_url )
    data = resp.json()
    if len(data) > 0:
      return data[0]['id']
    else:
      return None

  def send_notification(self, title, message):
    log.debug("Sending notification " + title + " " + message)
    data={}
    event_id=self.get_inprogress_event_id()
    if event_id != None:
      notification = self.Notification(self.name, event_id, title, message)
      notification.send()

  #################
  ## Openmiko stuff
  #####

  def update_thingino_info(self,data):
    self.last_updated = data['timestamp']
    self.version = data['version']
    self.ip = data['ip']
    self.collection_timestamp = data['collection_timestamp'] 
    uptime = data['uptime'] 
    self.uptime = uptime[uptime.find('up '):uptime.find(',  load')]
    state.set("sensor." + self.name + "_collection_timestamp", self.collection_timestamp)
    state.set("sensor." + self.name + "_uptime", self.uptime)
    state.set("sensor." + self.name + "_version", self.version)
    state.set("sensor." + self.name + "_local_ip", self.ip)
    state.set("sensor." + self.name + "_last_updated", self.last_updated)

  def reboot(self):
    command_array = [ "/sbin/reboot" ]
    log.info("Run " + str(command_array) + " on " + self.ip)
    output=execute_command_over_ssh(command_array, self.ip);
    log.info(output)

  def camera_state_factory(self):
   sensor_name = "binary_sensor." + self.name + "_status"
   log.info("Build state manager for " + sensor_name) 
   #@time_trigger("cron(*/10 * * * *)")
   #@time_trigger("cron(* * * * *)")
   def state_monitor():
     try: 
       log.info("Setting the state for " + self.name)
       last_updated=state.get("sensor." + self.name + "_last_updated")
       last_updated=datetime.strptime(last_updated,'%Y/%m/%d %H:%M:%S')
       if (last_updated - datetime.now()).total_seconds() > 300:
         #log.info(self.name + " last updated more than 5 minutes ago")
         pass
       else:
         #log.info(self.name + " last updated less than 5 minutes ago")
         pass
     except:
       log.info("No data for " + self.name)

   return state_monitor

  def thingino_invoke_api(self, api=None, value=None):
    url="http://" + self.ip + ":8081/api/" + api
    log.info(url)
    headers = {}
    headers["Content-Type"] = "text/html; charset=UTF-8"
    setvalue = "1"  if value == "on" else "0"
    data="value=" + str(setvalue)
    resp = task.executor(requests.put, url , data=data, headers=headers)
    log.info(resp)

  def camera_setting_toggle_sensor_factory(self, toggle_name):
   sensor_name = "input_boolean." + self.name + "_" + toggle_name
   log.debug("Build state trigger for " + sensor_name)
   @state_trigger(sensor_name)
   def func_toggle_sensor_state_change():
     current_state=state.get(sensor_name)
     if "nightvision" == toggle_name:
       command_array=["/usr/bin/nightmode.sh", current_state]
     else:
       command_array=["/usr/bin/" + toggle_name + ".sh", current_state]
     log.info("Set " + toggle_name + " to " + current_state + " for " + self.name)
     if "ir_cut" == toggle_name or "ir_led" == toggle_name:
       value = 1 if current_state == "on" else 0
       self.thingino_invoke_api(toggle_name, value)
     else:
       log.info(str(command_array))
       output=execute_command_over_ssh(command_array, self.ip, returnStdout=True)
       log.info(output)
   return func_toggle_sensor_state_change


  #################
  ## Notifications
  #####

  class Notification:
  
    def __init__(self, name,  event_id, title, message):
      self.name = name
      self.event_id = event_id
      self.title = title
      self.message = message
      self.data = self.build_attachments(event_id)

    def send(self):
      managed_notification(notification_name=self.name, title=self.title, message=self.message, data=self.data)

    def build_attachments(self, event_id):
      data = {}

      actions = []
      actions.append(self.build_action("Open external jpeg", Camera.EXTERNAL_FRIGATE_API_URL + "/events/" + self.event_id + "/snapshot.jpg"))
      actions.append(self.build_action("Open external mpeg", Camera.EXTERNAL_FRIGATE_API_URL + "/events/" + self.event_id + "/clip.mp4"))
      actions.append(self.build_action("Open internal jpeg", Camera.INTERNAL_FRIGATE_API_URL + "/events/" + self.event_id + "/snapshot.jpg"))
      actions.append(self.build_action("Open internal mpeg", Camera.INTERNAL_FRIGATE_API_URL + "/events/" + self.event_id + "/clip.mp4"))
      data['actions'] = actions
      log.debug(data)
      return data
    
    def build_action(self, title, uri):
      action = {}
      action['action'] = "URI"
      action['title'] = title
      action['uri'] = uri
      return action 


