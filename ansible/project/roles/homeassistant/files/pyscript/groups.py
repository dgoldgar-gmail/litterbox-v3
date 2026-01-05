import yaml

from registry import devices
from registry import entities

@service
def build_groups():
  light_groups = {}
  all_lights = {}
  all_lights['name'] = "All Lights"
  all_lights['entities'] = []
  light_groups['all_lights'] = all_lights
  for entity in entities:
    if entity.split(".")[0] == "light":  
      entity_obj = entities[entity]
      device_id = entity_obj.device_id 
      device_obj = devices[device_id]
      area_id = device_obj.area_id

      if area_id != None:
        light_group_name = (area_id.replace("_"," ")).title() + " Lights"
        light_group_id = area_id + "_lights"
        if light_group_id not in light_groups:
          light_group = {}
          light_groups[light_group_id] = light_group
          light_group = light_groups[light_group_id]
          light_group['name'] = light_group_name
          light_group['entities'] = []
          all_lights['entities'].append("group." + light_group_id)
        light_group['entities'].append(entity)
  log.info(yaml.dump(light_groups, sort_keys=False))
          


