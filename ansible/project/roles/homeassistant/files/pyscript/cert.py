from datetime import datetime, timedelta
from notify import managed_notification
from OpenSSL import crypto as c
import os

from basics import read_json_from_file
from states import set_state 

# TODO Get this path from the configuration yaml
cert_file_location="/config/cohabitrail-fullchain.pem"
@service
@time_trigger("cron(0 */6 * * *)")
@time_trigger("startup")
def get_certificate_expiry():
  pemfile=os.open(cert_file_location,os.O_RDONLY)
  pemstream=os.read(pemfile,10240)
  cert = c.load_certificate(c.FILETYPE_PEM, pemstream)
  expiry_datetime=cert.get_notAfter()
  expiry_datetime=expiry_datetime.decode("utf-8") 
  expiry_datetime=datetime.strptime(expiry_datetime,"%Y%m%d%H%M%SZ")
  now = datetime.now()
  comingsoon=now+timedelta(days=7) >= expiry_datetime
  delta = expiry_datetime - now
  set_state("sensor.certificate_expiry_date", str(expiry_datetime))
  set_state("sensor.certificate_days_left", str(delta.days))
  if comingsoon:
    title="Certificate Expiration Notice"
    message="Certificate will expire in " + str(delta.days) + " days (" + str(expiry_datetime) + ")"
    managed_notification(notification_name="cert", title=title, message=message)


@service
@time_trigger("cron(0 */6 * * *)")
@time_trigger("startup")
def get_certificate_data():
  pemfile=os.open(cert_file_location,os.O_RDONLY)                 
  pemstream=os.read(pemfile,10240)                                
  cert = c.load_certificate(c.FILETYPE_PEM, pemstream)

  subject=cert.get_subject()
  set_state("sensor.certificate_subject", str(subject))
  issuer=cert.get_issuer()
  set_state("sensor.certificate_issuer", str(issuer))
  version=cert.get_version()
  set_state("sensor.certificate_version", str(version))
  serial_number=cert.get_serial_number()
  set_state("sensor.certificate_serial_number", str(serial_number))
  pubkey=cert.get_pubkey()
  set_state("sensor.certificate_pubkey", pubkey)
  not_before=cert.get_notBefore()
  set_state("sensor.certificate_not_before", not_before.decode("utf-8"))
  signature_algorithm=cert.get_signature_algorithm()
  set_state("sensor.certificate_signature_algorithm", signature_algorithm.decode("utf-8"))
  has_expired=cert.has_expired()
  set_state("sensor.certificate_has_expired", str(has_expired))

  ext_count=cert.get_extension_count()               
  log.debug(ext_count)
  for i in range(0,ext_count):                       
    ext_data=str(cert.get_extension(i))   
    log.debug(str(i) + "=>" + ext_data)
    try:
      #set_state("sensor.certificate_extension_"+str(i), ext_data)
      pass
    except:
      pass


