from states import set_state

@service
def ble_data_service(data=None):
    #log.info(data)
    entity_name = None
    entity_class = None
    base_attrs = ["mac", "model", "name", "battery","rssi", "timestamp"]
    device_specific_attrs = []
    if data['model'] == "H5182":
      entity_type = "govee"
      entity_class = "meatometer"
      value_attr = "temp"
      device_specific_attrs = [ "temp", "set_point", "alarm", "status" ]
    elif data['model'] == "IBT-4XS":
      entity_class = "meatometer"
      entity_type = "inkbird"
      value_attr = "temp"
      device_specific_attrs = [ "temp"]
    elif data['model'] == "RD200V3":
      base_attrs = ["mac", "model", "name", "rssi", "timestamp"]
      entity_class = "radoneye"
      entity_type = data['model']
      value_attr = "latest_pci_l"
      device_specific_attrs = ['serial', 'firmware_version', 'latest_bq_m3', 'latest_pci_l', 'day_avg_bq_m3', 'day_avg_pci_l', 'month_avg_bq_m3', 'month_avg_pci_l', 'peak_bq_m3', 'peak_pci_l', 'counts_current', 'counts_previous', 'counts_str', 'uptime_minutes', 'uptime_str', 'display_unit', 'alarm_enabled', 'alarm_level_bq_m3', 'alarm_level_pci_l', 'alarm_interval_minutes' ]

    else:
      log.info("Unknown ble_data_service data: " + mac)  

    if entity_type is not None and entity_class is not None:
      for sensor in data['sensors']:
        entity_name = f"sensor.{entity_class}_{entity_type}_{data['name']}_{sensor}"
        set_state(entity_name, data['sensors'][sensor][value_attr])
        for attr in base_attrs:
          try:
            log.debug(f"{entity_name}.{attr} = {data[attr]}")
            state.setattr(f"{entity_name}.{attr}", data[attr])
          except:
            log.info(f"Failed setting {entity_name}.{attr}")
        for attr in device_specific_attrs:
          log.debug(f"{entity_name}.{attr} = {data['sensors'][sensor][attr]}")
          state.setattr(f"{entity_name}.{attr}", data['sensors'][sensor][attr])
      
     
