import homeassistant
import os
import uuid
import yaml

from basics import read_yaml_from_file

from registry import areas, devices, entities

@service
@time_trigger("cron(0 0 * * *)")
def update_scene_input_list():
  options=[]
  for entity in entities:
    if entity.startswith("scene"):
      options.append(entity)
  options.sort()
  input_select.set_options(entity_id="input_select.selected_scene",options=options)


@service
def activate_scene():
  selected_scene=state.get("input_select.selected_scene")
  scene.turn_on(entity_id=selected_scene)


@service
def create_group_scenes():
  groups_yaml=read_yaml_from_file("/config/yaml/groups.yaml",102400)
  #log.info(groups_yaml)  
  scenes = []
  for group in groups_yaml:
    scene = create_group_scene(group,"on")
    scenes.append(scene)
    scene = create_group_scene(group,"off")
    scenes.append(scene)
  log.info("\n" + yaml.safe_dump(scenes, sort_keys=False))
    
    
  
def create_group_scene(group_name, state_transition):
    scene = {}
    scene['id'] = uuid.uuid4().hex
    scene['name'] = group_name.replace("_"," " )  + " " + state_transition
    entities = {}
    scene['entities'] =  entities
    entities['state'] = state_transition
    return scene
  
  

