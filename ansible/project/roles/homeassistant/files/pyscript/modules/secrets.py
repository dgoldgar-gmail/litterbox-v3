
import os
import yaml

def get_secret(name):
  secrets=os.open("/config/secrets.yaml",os.O_RDONLY)
  secret_text=os.read(secrets,40960)
  secret_yaml=yaml.safe_load(secret_text)
  secret_value=secret_yaml[name]
  return secret_value
