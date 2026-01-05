from hosts import ping_host
from hosts import get_all_hosts

#@service
#@time_trigger("cron(*/5 * * * *)")
#@time_trigger("startup")
#def check_ping_states():
#  hosts=get_all_hosts(True)
#  for host in hosts:
#    log.info("Get ping state for host " + host)
#    try:
#      state.set("sensor.ping_state_" + host.replace("raspberry-",""), ping_host(host))
#    except:
#      log.info("Failed ping state check " + host)
#      state.set("sensor.ping_state_" + host.replace("raspberry-",""), "0")
  
