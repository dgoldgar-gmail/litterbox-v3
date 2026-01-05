
from notify import internal_managed_notification

@service
def icloudpd_alert(data):
  code=data['code']
  message=data['message']
  account=data['account']
  
  internal_managed_notification(title=f"ICloud PD authorization alert code {code} for {account}", message=message, data=None,  phone=True, persistent=True)
 
