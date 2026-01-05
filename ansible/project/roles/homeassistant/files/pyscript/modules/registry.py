
import homeassistant

entityreg=homeassistant.helpers.entity_registry.async_get(hass)
entities=entityreg.entities

devicereg=homeassistant.helpers.device_registry.async_get(hass)
devices=devicereg.devices

areareg=homeassistant.helpers.area_registry.async_get(hass)
areas=areareg.areas

def update_entity_id(id,new_id):
  entityreg.async_update_entity(entity_id=id, new_entity_id=new_id)

def update_entity_name(id,new_name):
  entityreg.async_update_entity(entity_id=id, name=new_name)

def update_device_name(id,new_name):
  devicereg.async_update_device(id, name=new_name)


def find_entites_for_device_id(device_id):
  return_list = []
  for entity_id in entities:
    if entities.get(entity_id).device_id == device_id:
      return_list.append(entities.get(entity_id))
  return return_list
