#
#from kasa.cli import cli
#from commands import execute_command
#import json
#
#@service
#def get_kasa_device_config():
#  command_array=["/usr/local/bin/kasa", "--json"]
#  output=execute_command(command_array)
#  output = json.loads(output)
#  keys = output.keys()
#  config_map = []
#  for key in keys:  
#    config_item = {}
#    config_item['ip'] = key
#    name=output[key]['system']['get_sysinfo']['alias']
#    config_item['name'] = name
#    # Lights - Game Room'
#    # light.lights_game_room
#    entity_id = "lights." + name.strip().replace(" - ","_").replace(" ","_").lower()
#    config_item['entity_id'] = entity_id
#    config_map.append(config_item)
#     
#  log.info(config_map)
#
#@service
#def get_kasa_device_ips():
#  command_array=["/usr/local/bin/kasa", "--json"]
#  output=execute_command(command_array)
#  log.info(json.loads(output).keys())
#  return json.loads(output).keys()
#
#
#@service
#def get_kasa_device_info(ip):
#  command_array=["/usr/local/bin/kasa", "--json", "--host", ip ]
#  output=execute_command(command_array)
#  json_data=json.loads(output)
#  log.info(json.dumps(json_data,indent=2))
#
#
##command_array=["kasa", "--host", ip, "wifi", "join", "-password", "password",  "SSID" ] 
