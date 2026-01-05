
from registry import entityreg

class TasmotaDevice:
  def __init__(self, device_obj):
    self.device = device_obj
    self.name = device_obj.name
    self.id = device_obj.id
    self.area_id = device_obj.area_id
    self.configuration_url = device_obj.configuration_url
    self.hw_version = device_obj.hw_version
    self.sw_version = device_obj.sw_version
    self.entities = []

  def dump(self):
    log.info(self.device)
    log.info(self.name)
    log.info(self.id)
    log.info(self.area_id)
    log.info(self.configuration_url)
    log.info(self.hw_version)
    log.info(self.sw_version)
    for entity in self.entities:
      entity.dump()
      log.info("")

  def add_entity(self, entity_info):
    aq_entity = self.TasmotaEntity(self, entity_info)
    self.entities.append(aq_entity)

  class TasmotaEntity:
    def __init__(self, parent_device, entity_info):
      try:
        log.info(device.name)
      except:
        pass
      self.name = parent_device.device.name
      
      self.device = parent_device
      self.id = entity_info.id
      self.unique_id = entity_info.unique_id
      self.entity_id = entity_info.entity_id
      self.name = parent_device.device.name.replace("-","_").lower()
      self.area_id = parent_device.area_id
      self.model = parent_device.device.model
      self.subtype = ""
      if entity_info.original_name != None:
        self.subtype = entity_info.original_name.replace(" ","_").lower()
      self.calculated_id = ""
      if self.name != None:
        self.calculated_id = "sensor." + self.name.replace("-","_").lower() + "_" + self.subtype

    def dump(self):
      log.info("\tname:  " + str(self.name))
      log.info("\tid: " + str(self.id))
      log.info("\tunique_id: " + str(self.unique_id))
      log.info("\tentity_id: " + str(self.entity_id))
      log.info("\tcalculated_id: " + str(self.calculated_id))
      log.info("\tarea_id: " + str(self.area_id))
      log.info("\tmodel: " + str(self.model))
      log.info("\tsubtype: " + str(self.subtype))

    def update_entity_id(self):
      if self.entity_id == self.calculated_id:
        return
      if self.model ==  "Sonoff S31":
        try:
          log.info("Update entity id from " + str(self.entity_id) + " to " + str(self.calculated_id))
          entityreg.async_update_entity(entity_id=self.entity_id, new_entity_id=self.calculated_id)
        except Exception as e:
          log.info(e)
          log.info("Failed resettin id for " + str(self.name))
      else:
        log.info("Skip updating id for " + str(self.name)) 



#def update_entity_name(id,new_name):
#  entityreg.async_update_entity(entity_id=id, name=new_name)
#
#def update_device_name(id,new_name):
#  devicereg.async_update_device(id, name=new_name)


