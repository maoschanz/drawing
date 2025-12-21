from select import select
from evdev import InputDevice, list_devices, ecodes, categorize

def previous_value(new_p=None):
    """
    There is a need to store event values from evdev,
    because it skips reporting if there is no change 
    on the event.
    So, the idea is to use the previous value when
    evdev skips reporting.
    """
    prev_p = getattr(previous_value, 'p_press', None)
    # This function either
    # a) reports the previous value (no argument)
    # or
    # b) stores a new value (given a suitable new value)
    # returns p_press
    if new_p is None:
        if prev_p is not None:
            p_press = prev_p  # use the stored value
        else:
            p_press = 0       # use 0 as initial value
            previous_value.p_press = 0   # store it
        return p_press
    else:
        if new_p >= 0:
            previous_value.p_press = new_p

def test():
    print("apitek_access")
    pressure = previous_value()  # initialise
    vid=0x08ca
    pid=0x0010
    devices=[InputDevice(dev) for dev in list_devices()]
    for dev in devices:
        if dev.info.vendor==vid and dev.info.product==pid:
            print(f"Found: {dev.name} at {dev.path}")
            # read list, write list, exception list
            r, w, x = select( [dev], [], [], 0.008) # 0.008 seconds timeout
            if dev in r: # device has readable data now
                print("reading..")
                for event in dev.read():
                    if   event.type == ecodes.EV_KEY:
                        pass
                    elif event.type == ecodes.EV_REL:
                        pass
                    elif event.type == ecodes.EV_ABS: # absolute value
                        if   event.code ==  1:
                            pass
                        elif event.code ==  2:
                            pass
                        elif event.code == 24:        # 24 is pressure
                            previous_value(new_p=event.value)
                        else:
                            print(f"EV_ABS code: {event.code}",
                                  f"value: {event.value}")
                    elif event.type == ecodes.EV_SYN: # synchronization event
                        pressure = previous_value()
                        print(f"evdev: {pressure}")
                        return pressure
            else: # timeout and no data to read
                pressure = previous_value()
                return pressure
