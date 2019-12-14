import datetime
import uuid


def json_serial(obj):
    if isinstance(obj, datetime.datetime):
        serial = obj.replace(tzinfo=datetime.timezone.utc).timestamp()
        return int(serial)

    if isinstance(obj, datetime.date):
        DAY = 24 * 60 * 60  # POSIX day in seconds (exact value)
        timestamp = (obj - datetime.date(1970, 1, 1)).days * DAY
        return timestamp

    if isinstance(obj, uuid.UUID):
        return str(obj)

    raise TypeError("Type %s not serializable" % type(obj))
