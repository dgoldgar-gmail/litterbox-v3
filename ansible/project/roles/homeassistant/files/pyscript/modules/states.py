

def set_state(sensor=None, value=None, attrs=None):
  if attrs is None:
    log.debug("Set state of " + sensor + " to value " + str(value) )
    state.set(sensor, value)
  else:
    log.debug("Set state of " + sensor + " to value " + str(value) + " with attrs " + ' '.join(map(str, attrs)) )
    state.set(sensor,value,attrs)


def get_state(sensor=None):
  return state.get(sensor)
