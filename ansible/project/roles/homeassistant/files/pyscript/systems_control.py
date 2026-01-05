from decimal import Decimal       
from packaging import version
from requests.structures import CaseInsensitiveDict

import json
import os                                                          
import re                                                          
import requests                                                         

from basics import read_json_from_file
from commands import execute_command
from registry import devices
from registry import entities
#from secrets import get_secret
from states import set_state

@service
def execute_system_command(command=None, system_type=None, system_name=None):

  ip =""
  if system_name=="dave":
    ip="192.168.50.200"
  elif system_name=="sam":
    ip="192.168.50.119"
  else:
    log.info("Supported system_name options are 'dave' and 'sam'");
    return;
 

  shell_command = "" 
  key= ""
  user = ""
  if system_type is None:
    log.info("System type can be 'linux' or 'windows'")
    return
  elif system_type=="windows":
    key = "windows.key"
    user = "dgoldgar"
    if command is None: 
      log.info("Command options are 'Shutdown', 'Reboot', or 'Suspend'")
      return
    elif command == "Shutdown":
      shell_command = "shutdown /s"      
    elif command == "Reboot":
      shell_command = "shutdown /r"      
    elif command == "Suspend":
      shell_command = "psshutdown -d  -t 5 /accepteula"      
    else:
      log.info("Command options are 'Shutdown', 'Reboot', or 'Suspend'")
      return
  elif system_type=="linux":
    key = "id_rsa"
    user = "root"
    if command is None: 
      log.info("Command options are 'Shutdown', 'Reboot', or 'Suspend'")
      return
    elif command == "Shutdown":
      #shell_command = "systemctl halt"      
      shell_command = "init 0"      
    elif command == "Reboot":
      shell_command = "systemctl reboot"
    elif command == "Suspend":
      shell_command = "systemctl suspend"      
    else:
      log.info("Command options are 'Shutdown', 'Reboot', or 'Suspend'")
      return
  else:
    log.info("System type can be 'linux' or 'windows'")
    return
  
  command_array = ["/usr/bin/ssh", "-t", "-t", "-t",
                              "-o", "BatchMode=yes",
                              "-o", "ConnectTimeout=5",
                              "-o", "UserKnownHostsFile=/dev/null",
                              "-o", "StrictHostKeyChecking=no",
                              "-i", "/config/.ssh/" + key,
                              user + "@" + ip,
                              shell_command ]

  try:
    execute_command(command_array)
    log.info("Successfully executed " + shell_command + " on " + system_type + " with " + ip + " user=" + user + ",key=" + key   )
  except Exception as e:
    log.info("Failed to execute " + shell_command + " on " + system_type + " with " + ip + " user=" + user + ",key=" + key )
    log.error(e)

#@service
#@time_trigger("cron(*/10 * * * *)")
#@time_trigger("startup")
#def get_system_info():
#
#  command_array = ["/usr/bin/free"]
#  lines=execute_command(command_array,True)
#  
#  mem_percent_used=0
#  swap_percent_used=0
#  for line in lines:
#    line=line.decode("utf-8") 
#    tokens=re.split(r'\s+', line)
#    if tokens[0] == "Mem:":
#      mem_total=tokens[1]
#      mem_used=tokens[2]
#      mem_percent_used=Decimal(mem_used)/Decimal(mem_total)
#      mem_percent_used=mem_percent_used*100
#    if tokens[0] == "Swap:":
#      swap_total=tokens[1]
#      swap_used=tokens[2]
#      swap_used=Decimal(swap_used)
#      swap_total=Decimal(swap_total)
#      swap_percent_used=swap_used/swap_total
#      
#      swap_percent_used=swap_percent_used*100
#  set_state("sensor.swap_percent_used",round(swap_percent_used,2),{"friendly_name":"Swap used", "unit_of_measurement": "%"})
#  set_state("sensor.memory_percent_used",round(mem_percent_used,2),{"friendly_name":"Memory used", "unit_of_measurement": "%"})
#
#
#  disk_percent_used=0
#  command_array = ["/bin/df", "-h"]
#  lines=execute_command(command_array,True)
#  for line in lines: 
#    line=line.decode("utf-8") 
#    tokens=re.split(r'\s+', line) 
#    #['Filesystem', 'Size', 'Used', 'Available', 'Use%', 'Mounted', 'on', '']
#    if tokens[0] == "overlay": 
#      size=tokens[1].strip('G')
#      used=tokens[2].strip('G')
#      disk_percent_used=Decimal(used)/Decimal(size)
#      disk_percent_used=disk_percent_used*100
#  set_state("sensor.disk_usage",round(disk_percent_used,2),{"friendly_name":"Disk Usage", "unit_of_measurement": "%"})
# 
  uptime=""
  command_array = ["/usr/bin/uptime"]
  lines=execute_command(command_array,True)
  for line in lines: 
    uptime=line.decode("utf-8") 
  set_state("sensor.uptime",uptime,{"friendly_name":"Uptime"})
#
#    
#  cpu_idle=""
#  command_array = ["/bin/iostat","-c"]
#  lines=execute_command(command_array,True)
#  data=lines[3]
#  data=data.decode("utf-8")
#  tokens=re.split(r'\s+', data)
#  cpu_idle=tokens[6]
#  cpu_idle=Decimal(cpu_idle)
#  cpu_used=100-cpu_idle
#  set_state("sensor.cpu_idle",round(cpu_idle,2),{"friendly_name":"CPU Idle", "unit_of_measurement":"%"})
#  set_state("sensor.cpu_used",round(cpu_used,2),{"friendly_name":"CPU Used", "unit_of_measurement":"%"})


@service
def set_linux_uptime(name=None, ip=None):
  command_array = ["/usr/bin/ssh", "-t", "-t", "-t",
                              "-o", "BatchMode=yes",
                              "-o", "ConnectTimeout=5",
                              "-o", "UserKnownHostsFile=/dev/null",
                              "-o", "StrictHostKeyChecking=no",
                              "-i", "/config/.ssh/id_rsa",
                              "root@" + ip, "uptime" ]

  exit_code=0
  output_string=""
  try:
    output_string=(execute_command(command_array)).strip()
    if output_string == "":
      exit_code=1
      output_string = "Not running"
    else:
      exit_code=0
  except Exception as e:
    output_string = "Not running"
    exit_code = 1

  set_state("sensor." + name + "_linux_status", exit_code)
  set_state("sensor." + name + "_linux_uptime", output_string)

@service
def set_ping_state(name=None, ip=None):

  if name is None:
    log.debug(f"===== name is required for ping")
    return

  if ip is None:
    log.debug(f"===== ip is required for ping")
    return

  command_array=["/usr/sbin/arping", "-c", "1", "-w", "5", ip]
  try:
    set_state("sensor." + name + "_system_status", 0)
  except:
    set_state("sensor." + name + "_system_status", 1)
    
  
  windows_up = 1
  try:
    windows_up = state.get("sensor." + name + "_windows_status") 
  except NameError:   
    windows_up = 1


  linux_up = 1
  try:
    linux_up = state.get("sensor." + name + "_linux_status") 
  except NameError:   
    linux_uptime = 1

  wakeable=0
  if windows_up=="1" and linux_up=="1":
    wakeable=0
  else :
    wakeable=1

  set_state("sensor." + name + "_system_wakeable", wakeable)

@service
def set_windows_uptime(name=None, ip=None):
  command_array= ["/usr/bin/ssh", "-t", "-t", "-t",
                              "-o", "BatchMode=yes",
                              "-o", "ConnectTimeout=5",
                              "-o", "UserKnownHostsFile=/dev/null",
                              "-o", "StrictHostKeyChecking=no",
                              "-i", "/config/.ssh/windows.key",
                              "dgoldgar@" + ip,
                              "systeminfo" ]
  exit_code=0
  output_string=""
  try:
    output_string=execute_command(command_array)
    if output_string == "":
      output_string = "Not running"
      exit_code = 1
    else:
      match = re.search(r'^System Boot Time:(.*)$', output_string, re.MULTILINE)
      output_string = (match.group(1)).strip()
      exite_codee = 0
  except Excepiton as e:                 
    exit_code = 1
    output_string = "Not running"

  set_state("sensor." + name + "_windows_status", exit_code)
  set_state("sensor." + name + "_windows_uptime", output_string)

