
from collections import Counter
from send_notification import send_email_whatsapp_notification


def send_notification_main(shared_dict, phone, email):
    if shared_dict["permission_to_send_alert"]:
        msg = f"Motion detected at {shared_dict['time_stamp'].strftime("%d-%b-%Y, %I:%M:%S %p")}."
        subject = f"Reliant Watcher Notification - {msg}"
        if not isinstance(shared_dict["OD_det_obj_info_for_alert"], Counter):
            raise ValueError("Object info for alert is not a Counter object.")
        objs_counter = shared_dict["OD_det_obj_info_for_alert"]
        if not sum(objs_counter.values()) == 0:
            keys = list(objs_counter.keys())
            len_of_keys = len(keys)
            if len_of_keys == 1:
                msg+= f"\n{objs_counter[keys[0]]} {keys[0]} detected in the scene."
            else:
                for i in range(len_of_keys):
                    if i == 0:
                        msg+= f"\n{objs_counter[keys[i]]} {keys[i]}"
                    elif i == len_of_keys - 1:
                        msg+= f" and {objs_counter[keys[i]]} {keys[i]} detected in the scene."
                    else:
                        msg+= f", {objs_counter[keys[i]]} {keys[i]}"
        print(f"Sending notification: {msg}")
        send_email_whatsapp_notification(subject, msg, phone, email)
        shared_dict["permission_to_send_alert"] = False
        shared_dict["OD_det_obj_info_for_alert"] = Counter()