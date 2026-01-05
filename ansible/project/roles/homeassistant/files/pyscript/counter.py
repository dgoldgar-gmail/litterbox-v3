
from registry import entities
from decimal import Decimal 

@service
def increment_counter(entity_id=None):
  ent_state=state.get(entity_id)
  ent_state = Decimal(ent_state)+1
  state.set(entity_id,ent_state)
  
@service
def decrement_counter(entity_id=None):
  ent_state=state.get(entity_id)
  ent_state = Decimal(ent_state)-1
  state.set(entity_id,ent_state)
  
