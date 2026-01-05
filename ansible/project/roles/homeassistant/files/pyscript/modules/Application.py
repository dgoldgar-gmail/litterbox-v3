from basics import read_json_from_file
from basics import read_yaml_from_file
from basics import write_yaml_file
from commands import execute_command
from commands import execute_command_over_ssh
from notify import internal_managed_notification
from registry import devices
from registry import entities
from secrets import get_secret
from states import set_state
from notify import managed_notification

from datetime import datetime, timedelta
import json
import os
import re
import requests
import traceback 
import yaml

class Application:
  app_defs = []

  def __init__(self, app_json):
    self.update(app_json)

  def update(self, app_json):
    self.hosts = []
    self.obj_ts = datetime.now()
    self.json = app_json
    self.name = app_json['name']
    self.managed = app_json['managed']
    self.notify_version = app_json['notify_version']
    self.latest_version = state.get("update.frigate_server.latest_version") if self.name == "frigate" else app_json['latest_version']
    self.hosts_json = app_json['hosts']
    for host in self.hosts_json:
      try:
        host_info=self.hosts_json[host]
        host_obj = self.Host(self.name, host, host_info)
        if self.name == "frigate":
          host_obj.current_version = state.get("update.frigate_server.installed_version")
        self.hosts.append(host_obj)
      except Exception as e:
        log.info("Exception initializing host " + host + " for app " + self.name )
    self.update_state()

  def update_state(self):
    for host in self.hosts:
      try:
        version_info = host.current_version
        current_version=host.current_version
        latest_version=self.latest_version
        container_state=host.container_state
        container_status=host.container_status
        container_image=host.container_image
        container_created_at = host.container_created_at
        collection_timestamp = host.collection_timestamp
       
        note_title = None 
        note_message = None

        if host.host_state == "0":
          version_info="N/A"
          icon="mdi:alert-outline"
          note_title = host.note_title_host_down
          note_message = "The host " + host.name + " is down, making " + self.name + " unavailabe there."
        elif latest_version == current_version:
          version_info=latest_version
          icon="mdi:check"
        elif host.container_state != "running":
          version_info="N/A"
          icon = "mdi:alert-box-outline"
          note_title = host.note_title_container_down
          note_messsage = "The docker container for " + self.name + " is not running on host " + host.name + "."
        else:
          version_info = "( ↑ " + latest_version + " ↑ ) " + current_version
          icon = "mdi:package-up"
          note_title = host.note_title_update_available
          note_message = "Update from " + current_version + " to " + latest_version + " can be applied to " + self.name + " on " + host.name + "."

        if note_title != None:
          managed_notification(notification_name=None, title=note_title, message=note_message, data=None)
        else:
          host.clear_notifications()

        set_state(self.get_sensor_name(host.name, self.name, "current_version"), str(current_version))
        set_state(self.get_sensor_name(host.name, self.name, "state"), str(container_state))
        set_state(self.get_sensor_name(host.name, self.name, "status"), str(container_status))
        set_state(self.get_sensor_name(host.name, self.name, "image"), str(container_image))
        set_state(self.get_sensor_name(host.name, self.name, "created_at"), str(container_created_at))
        set_state(self.get_sensor_name(host.name, self.name, "collection_timestamp"), str(collection_timestamp))
        set_state(self.get_sensor_name(host.name, self.name, "version_info"), str(version_info), { "icon": icon })
      except Exception as e:
        log.info(e)
        log.info("Failed setting states for " + self.name + " on host " + host.name)
        host.dump()

  def dump(self):
    log.info("name: " + str(self.name))
    log.info("\tobj_ts:  " + str(self.obj_ts))
    log.info("\tlatest_version: " + str(self.latest_version))
    for host in self.hosts:
      host.dump()

  def get_sensor_name(self, host, container, name):
    sensor_name = "sensor." + host.replace("raspberry-","") + "_" + container.replace("-","_") + "_" + name
    sensor_name = sensor_name.replace("ubuntu-","") 
    return sensor_name

  def schedule_update(self, host):
    log.info("Scheduling " + self.name + " for upgrade on " + host)
    if self.managed == "true":
      version_map=read_yaml_from_file("/config/scheduled_upgrades.yaml")
      if version_map == None:
        version_map = {}
      app_host_version_map = {}
      if  host in version_map:
        app_host_version_map =  version_map[host]
      version_map[host] = app_host_version_map
      app_host_version_map[self.name] = str(self.latest_version)
      write_yaml_file("/config/scheduled_upgrades.yaml",version_map)

  def control(self, host, command):
    log.info("Invoked service " +  command + " for app " + self.name + " on " + host)
    if command == "upgrade":
      command_array = [ "/opt/LITTERBOX/bin/start_containerized_app.py", self.name, self.latest_version ]
      output=execute_command_over_ssh(command_array, host, username="root")
    else:
      command_array = [ "/usr/bin/docker", command, self.name ]
      output=execute_command_over_ssh(command_array, host, username="root")
      log.info(output)

  @staticmethod
  def get_tasmota_device_versions_map():
    versions = {}
    for device in devices:
      device_obj=devices.get(device)
      if device_obj.manufacturer == 'Tasmota' and not device_obj.model == "ESP32-DevKit":
        log.debug(device_obj.id + " = " + device_obj.name + " version => " + device_obj.sw_version)
        versions[device_obj.name] = "v" + device_obj.sw_version
    return versions

  @staticmethod
  def get_telegraf_current_version():
    command_array=["/usr/bin/docker", "exec", "telegraf", "/usr/bin/telegraf", "--version" ]
    output=execute_command(command_array)
    output=output.split(" ")[1]
    return output.strip()

  @staticmethod
  def get_application_json():
    if  len(Application.app_defs) == 0:
      log.info("Loading file")
      Application.app_defs=read_json_from_file("/config/pyscript/modules/applications.json", 20480,os.O_RDONLY)
    return Application.app_defs


  class Host:
    def __init__(self, app, host, host_info):
      self.name = host
      self.host_info = host_info
      self.host_state = host_info['host_state']
      self.current_version = host_info['current_version']
      self.collection_timestamp = host_info['collection_timestamp']

      self.note_title_host_down = app.title() + " - " + self.name + " Down"
      self.note_title_container_down = app.title() + " Down on " + self.name
      self.note_title_update_available = "Update Available for " + app.title() + " on " + self.name

      self.container_status = "NOT SET"
      self.container_state = "NOT SET"
      self.container_image = "NOT SET"
      self.container_created_at = "NOT SET"
      docker_info = host_info['docker']
      if host_info['host_state'] == "0":
        self.container_status = "Host Down"
        self.container_state = "Host Down"
        self.container_image = None
        self.container_created_at = None
        self.current_version = None
      elif docker_info == None:
        self.current_version = None
      else:
        self.container_status = docker_info['status']
        self.container_state = docker_info['state']
        self.container_image = docker_info['image']
        self.container_created_at = docker_info['created_at']

    def clear_notifications(self):
      #log.info("Clear: " + self.note_title_host_down)
      #log.info("Clear: " + self.note_title_container_down)
      #log.info("Clear: " + self.note_title_update_available)
      persistent_notification.dismiss(notification_id=self.note_title_host_down)
      persistent_notification.dismiss(notification_id=self.note_title_container_down)
      persistent_notification.dismiss(notification_id=self.note_title_update_available)
  
    def dump(self):
      log.info("\t" + self.name)
      log.info("\t\t" + self.collection_timestamp)
      log.info("\t\t" + str(self.current_version))
      log.info("\t\t" + str(self.container_created_at))
      log.info("\t\t" + str(self.container_state))
      log.info("\t\t" + str(self.container_status))
      log.info("\t\t" + str(self.container_image))
            


