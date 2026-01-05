from basics import read_yaml_from_file
from commands import execute_command

def get_pi_hosts():
  hosts=read_yaml_from_file("/config/pyscript/modules/hosts.yaml")
  return hosts['pi']

def get_ubuntu_hosts():
  hosts=read_yaml_from_file("/config/pyscript/modules/hosts.yaml")
  return hosts['ubuntu']


def get_all_hosts(include_cameras=False):
  pihosts=get_pi_hosts()
  ubuntu_hosts= get_ubuntu_hosts()
  all_hosts=[]
  all_hosts.extend(pihosts)
  all_hosts.extend(ubuntu_hosts)
  if include_cameras:
    pass
  return all_hosts

def ping_host(host):
  command_array = [ "/bin/ping", "-q", "-c", "1",  host ]
  output=execute_command(command_array, False, False)
  output=output.split(",")[1]
  output=output.split(" ")[1]
  return output
