
def internal_managed_notification(title=None, message=None, data=None,  phone=True, persistent=True):
  log.debug("Notification - title=>" + str(title) + " message=>" + str(message) + " data=>"  + str(data) + " phone=>" + str(phone) + " persistent=>" + str(persistent))
  phone_notification_enabled = True if state.get("input_boolean.global_phone_notifications_enabled_flag") == "on" else False
  if phone_notification_enabled ==  True and phone == True:
    if data == None:
      notify.Daves_Alert_Group(message=str(message), title=str(title))
    else:
      notify.Daves_Alert_Group(message=str(message), title=str(title), data=data)
  if persistent == True:
    if data == None:
      persistent_notification.create(message=str(message), title=str(title), notification_id=title)
    else:
      link_lines = []
      for action in data.get('actions', []):
          link_lines.append(f"{action['title']}: {action['uri']}")
      full_message = f"{message}\n" + "\n".join(link_lines)

      persistent_notification.create(message=str(full_message), title=str(title), notification_id=title)


def managed_notification(notification_name=None, title=None, message=None, data=None):
    log.debug("NOTIFICATTION: notification_name=> " + str(notification_name) + ";  title=>" + str(title) + " message=>" + str(message) + " object=>"  + str(data) )

    if notification_name == None:
      phone_control_value = False
      persistent_control_value = True
    else:     

      phone_control = "input_boolean." + notification_name + "_phone_notifications_enabled" 
      phone_control_value = True if state.get(phone_control) == "on" else False

      persistent_control = "input_boolean." + notification_name + "_persistent_notifications_enabled" 
      persistent_control_value = True if state.get(persistent_control) == "on" else False


    internal_managed_notification(title=title, message=message, data=data,  phone=phone_control_value, persistent=persistent_control_value)

