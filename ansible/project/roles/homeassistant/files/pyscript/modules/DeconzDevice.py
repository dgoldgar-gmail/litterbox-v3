
from registry import entityreg

class DeconzDevice:
  def __init__(self, device_obj):
    self.device = device_obj
    self.name = device_obj.name
    self.id = device_obj.id
    self.area_id = device_obj.area_id
    self.entities = []
    pass


  def dump(self):
    log.info(self.name)
    log.info(self.id)
    log.info(self.area_id)
    for entity in self.entities:
      entity.dump()
      log.info("")


  def add_entity(self, entity_info):
    aq_entity = self.DeconzEntity(self, entity_info)
    self.entities.append(aq_entity)



  class DeconzEntity:
    def __init__(self, device_obj, entity_info):
      self.name = entity_info.name
      self.device = device_obj
      self.id = entity_info.id
      self.unique_id = entity_info.unique_id
      self.entity_id = entity_info.entity_id
      self.name = entity_info.name
      self.area_id = device_obj.area_id
      self.model = device_obj.device.model
      self.derive()
      try:
        self.calculated_id = self.entity_id_prefix + "." + self.main_type + "_" + self.area_id + "_" + self.subtype
      except:
        log.info("No area for " + self.entity_id)
        self.calculated_id = None

    def derive(self):
      if self.model == "lumi.sensor_motion.aq2" or self.model == "lumi.motion.agl04":
        self.subtype = self.unique_id.split("-")[3]
        self.main_type = "motion_sensor"
        if "presence" == self.subtype:
          self.entity_id_prefix = "binary_sensor"
        elif "duration" == self.subtype:
          self.entity_id_prefix = "number"
        else:
          self.entity_id_prefix = "sensor"
      elif self.model == "lumi.sensor_magnet.aq2":
        #log.info(self.device.device.labels)
        self.area_id = next(iter(self.device.device.labels))
        self.subtype = self.unique_id.split("-")[3]
        self.main_type = "door_sensor"
        if "open" == self.subtype:
          self.entity_id_prefix = "binary_sensor"
        else:
          self.entity_id_prefix = "sensor"
      elif self.model == "lumi.weather":
        self.subtype = self.unique_id.split("-")[3]
        self.entity_id_prefix = "sensor"
        self.main_type = "thermometer"
      elif self.model == "lumi.remote.b1acn01":
        self.subtype = self.unique_id.split("-")[3]
        self.entity_id_prefix = "sensor"
        self.main_type = "button"
      elif self.model == "lumi.sensor_cube.aqgl01":
        self.subtype = self.unique_id.split("-")[3]
        self.entity_id_prefix = "sensor"
        self.main_type = "magic_cube"
      elif self.model == "E1C-NB7":
        self.subtype = ""
        self.entity_id_prefix = "sensor"
        self.main_type = "power_plug"
      elif self.model == "PHDL00":
        self.subtype = None
        self.entity_id_prefix = "sensor"
        self.main_type = "daylight"
      elif self.model == "deCONZ group":
        self.subtype = None
        self.entity_id_prefix = "sensor"
        self.main_type = "deCONZ"
      elif self.model == "LWA029":
        self.subtype = "bulb"
        self.entity_id_prefix = "sensor"
        self.main_type = "light_bulb"
      else:
        self.entity_id_prefix = None
        self.main_type = None
        self.subtype = self.unique_id.split("-")[3]
       
    def dump(self):
      log.info("\t" + str(self.name))
      log.info("\t" + str(self.id))
      log.info("\t" + str(self.unique_id))
      log.info("\t" + str(self.entity_id))
      log.info("\t" + str(self.calculated_id))
      log.info("\t" + str(self.name))
      log.info("\t" + str(self.area_id))
      log.info("\t" + str(self.model))
      log.info("\t" + str(self.entity_id_prefix))
      log.info("\t" + str(self.main_type))
      log.info("\t" + str(self.subtype))

    def update_entity_id(self):
      try:
        log.info("Update entity id from " + self.entity_id + " to " + str(self.calculated_id))
        ## All the Aqara stuff seems to be correct now  - TODO:  There's sengleds and some random other stuff to manage
        if self.model in ["lumi.sensor_motion.aq2", "lumi.motion.agl04", "lumi.sensor_magnet.aq2" , "lumi.weather", "lumi.sensor_cube.aqgl01", "lumi.remote.b1acn01" ]:
          entityreg.async_update_entity(entity_id=self.entity_id, new_entity_id=self.calculated_id)
      except Exception as e:
        log.info("Failed resettin id for " + self.name)



#def update_entity_name(id,new_name):
#  entityreg.async_update_entity(entity_id=id, name=new_name)
#
#def update_device_name(id,new_name):
#  devicereg.async_update_device(id, name=new_name)



