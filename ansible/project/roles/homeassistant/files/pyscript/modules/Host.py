



class Host:
  def __init__(self, data):
    self.name = data['name']
    self.status = data['status']
    self.type = data['type']
    self.temp = data['temp']
    self.volts = data['volts']
    self.mounts = []
    self.nvme_devices = []
    for mount in data['mounts']:
      self.mounts.append(self.Mount(mount))
    for nvme in data['nvme_devices']:
      self.nvme_devices.append(self.NvmeDevice(nvme))

  def update(self, collection_timestamp):
    data = {}
    data['type'] = self.type
    data['timestamp'] = collection_timestamp 
    sensor = "sensor.host_" + self.name.replace("-","_")
    status = "UP" if int(self.status) == 1 else "DOWN"
    if self.type ==  "raspberry-pi":
      data['cpu_temp'] = self.temp
      data['cpu_volts'] = self.volts
      
    log.debug("Set sensor " + sensor + " to " + status + " with data " + str(data))
    state.set(sensor, status, data)


    if self.type == "ubuntu":
      for nvme in self.nvme_devices:
        sensor = "sensor.nvme_" + self.name.replace("-","_") + "_" + nvme.name.split("/")[2] + "_temp"
        state.set(sensor, nvme.temp, {'timestamp': collection_timestamp})
      
    for mount in self.mounts:
      sensor = "sensor.mount_" + self.name.replace("-","_") + "_" + mount.name.split("/")[2] + "_details"
      data = {}
      data['temperature_celsius'] = mount.temp
      data['media_wearout_indicator'] = mount.wear
      data['ssd_life_left'] = mount.life
      data['timestamp'] =  collection_timestamp
      state.set(sensor,  mount.name, data)

  class Mount:
    def __init__(self, data):
      self.name = data['name']
      self.temp = data['Temperature_Celsius'] if 'Temperature_Celsius' in data else None
      self.wear = data['Media_Wearout_Indicator'] if 'Media_Wearout_Indicator' in data else None
      self.life = data['SSD_Life_Left'] if 'SSD_Life_Left' in data else None

    def dump(self):
      log.info("\t\t" + self.name)
      log.info("\t\t\t" + str(self.temp))
      log.info("\t\t\t" + str(self.wear))
      log.info("\t\t\t" + str(self.life))
    
  class NvmeDevice:
    def __init__(self, data):
      self.name = data['name']
      self.temp = data['temp']

    def dump(self):
      log.info("\t\t" + self.name + "=>" + self.temp)


