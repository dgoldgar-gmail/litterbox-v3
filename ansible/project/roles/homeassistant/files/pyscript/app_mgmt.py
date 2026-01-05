from Application import Application
from Host import Host
from basics import read_json_from_file
from commands import execute_command_over_ssh
from states import set_state

import homeassistant
import json
import os

application_definitions = {}
host_definitions = {}

#@service
#def test_get_app_json():
#  json_val = Application.get_application_json()
#  log.info(json_val)

def get_application(name, data=None):
  global application_definitions 
  #log.info("Getting app : " + name ) 
  #log.info("From " + str(application_definitions))
  application_definition = None
  if name in application_definitions:
    application_definition = application_definitions[name]
  else:
    if data == None:
      application_definition = None
    else:
      application_definition = Application(data)
      #log.info("Created app object " + data['name'])
      application_definitions[name] = application_definition
  return application_definition

def get_host(name, data=None):
  global host_definitions 
  host_definition = None
  if name in host_definitions:
    host_definition = host_definitions[name]
  else:
    if data == None:
      host_definition = None
    else:
      host_definition = Host(data)
      host_definitions[name] = host_definition
  return host_definition

@service 
def schedule_containerized_app_update(appname=None, apphost=None):
  application_def = get_application(appname)
  application_def.schedule_update(apphost)


# This service gets called every ten minutes by a cron job
# that delivers a payload with host and app information 
#
@service
def ha_assistant(data):
  collection_timestamp = data['collection_timestamp']
  global application_definitions
  if 'hosts' in data:
    for host in data['hosts']:
      host_info = data['hosts'][host]
      host = get_host(host, host_info)
      host.update(collection_timestamp)
  if 'apps' in data:
    for app in data['apps']:
      log.debug(app)
      app_name = app['name']
      try:
        log.debug("Updating app " + app_name + " " + str(app))
        app_obj=get_application(app_name, app)
        app_obj.update(app) #, collection_timestamp)
      except Exception as e:
        log.info("Exception building app object: " + app_name, e)
  if 'radoneye' in data:
    #log.info(data['radoneye'])
    for eyes in data['radoneye']:
      for eye in eyes:
        log.info(eye)
        #log.info(eye['serial'])
        #log.info(eye['latest_pci_l'])
      set_state("sensor.radoneye_" + eye['location'] + "_level", eye['latest_pci_l'])
      
   
@service
def control_containerized_app(command, apphost, appname):
  application_def = get_application(appname)
  application_def.control(apphost,command)

