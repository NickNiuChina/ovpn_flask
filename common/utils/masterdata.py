import hashlib

def encode_tuple(t, sep='_'):
    """
    SHA1 encodes a tuple of strings joining them with a separator
    Args:
        t: string tuple
        sep: separator

    Returns: hexdigest

    """
    return hashlib.sha1(sep.join(t).encode('UTF_8')).hexdigest()

def encode_device_rp(supervisor_id, device_id, source_system_id):
    """
    SHA1 encode RemotePro device
    Args:
        supervisor_id: supervisor id
        device_id: device id
        source_system_id: source system id

    Returns: device UID

    """
    return encode_tuple([str(source_system_id), str(supervisor_id), str(device_id)])

def encode_device_tera(device_id, source_system_id=0, sub_device_id=0):
    """
    SHA1 encode Tera device
    Args:
        device_id: device id
        source_system_id: source system id (default 0)
        sub_device_id: sub device id (default 0)

    Returns: device UID

    """
    return encode_tuple([str(source_system_id), str(sub_device_id), str(device_id)])

def encode_supervisor(supervisor_id, source_system_id):
    """
    
    Args:
        supervisor_id:
        source_system_id:
        uuid: generate uuid instead of sha1

    Returns:

    """
    return encode_tuple(["supervisor", str(source_system_id), str(supervisor_id)])


def encode_plant(plant_id, source_system_id):
    """

    Args:
        plant_id:
        source_system_id:

    Returns:

    """
    return encode_tuple(["plant", str(source_system_id), str(plant_id)])