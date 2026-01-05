
import json
import os
import yaml

def read_yaml_from_file(file_name, buffer_size=1024, flags=os.O_RDONLY):
  file_handle=None
  yaml_response=None
  str_val = None
  try:
    file_handle=os.open(file_name, flags)
    str_val=os.read(file_handle,buffer_size)
    yaml_response=yaml.safe_load(str_val)
  except:
    log.info("Failed to convert file " + file_name + " to yaml [" + str(str_val) + "]") 
  finally:
    if os.path.isfile(file_name):
      os.close(file_handle)
  return yaml_response

def read_json_from_file(file_name, buffer_size=1024, flags=os.O_RDONLY):
  file_handle=None
  json_str=None
  str_val = None
  try:
    file_handle=os.open(file_name, flags)
    str_val=os.read(file_handle,buffer_size)
    json_str=json.loads(str_val)
  except:
    log.info("Failed to convert file " + file_name + " to json [" + str(str_val) + "]") 
  finally:
    if os.path.isfile(file_name):
      os.close(file_handle)
  return json_str

def write_json_file(file_name, json_content):
  json_object = json.dumps(json_content, indent=4)

  if os.path.isfile(file_name): 
    os.remove(file_name)

  json_file=None
  try: 
    json_file=os.open(file_name, os.O_CREAT|os.O_RDWR)
    os.write(json_file,str.encode(json_object))
  except:
    log.info("Failed to write json to file " + file_name )
  finally:
    os.close(json_file)


def write_yaml_file(file_name, contents):
  log.info("Write " + str(contents) + " to file named " + file_name)
  yaml_file=None
  try:
    yaml_file=os.open(file_name,os.O_CREAT|os.O_RDWR)
    yaml_content = yaml.dump(contents)
    os.write(yaml_file,str.encode(yaml_content))
  except e as Exception:
    log.info(e) 
    log.info("failed to write yaml to file " + file_name)


