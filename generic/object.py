store = {}


class Object:
    @classmethod
    def grab_or_create(cls, obj_id, *args, **kwargs):
        if cls.__name__ not in store:
            store[cls.__name__] = {}
        instances = store[cls.__name__]
        if obj_id in instances:
            instance = instances[obj_id]
            if cls.__name__ == 'DeezerShow':        # else deezer.episode overwrites
                return instance                     # some tags, so grab show first
            instance.set_values(*args, **kwargs)    # then episodes
            return instance
        else:
            instance = cls(*args, **kwargs)
            instances[obj_id] = instance
            return instance

    @classmethod
    def from_raw_data(cls, raw_data):
        return cls(raw_data=raw_data)

    def __init__(self, *args, **kwargs):
        self.set_values(*args, **kwargs)
