import abc

import polar as p


class Serializer:
    def load(self, raw):
        pass

    def dump(self, obj):
        pass


JSON_CUSTOM_SERIALIZERS = {}
JSON_CUSTOM_SERIALIZERS_BY_NAME = {}
JSON_CUSTOM_BASE = {}


def register(obj):
    p = 0

    def f(o):
        JSON_CUSTOM_SERIALIZERS[obj] = o()
        JSON_CUSTOM_SERIALIZERS_BY_NAME[obj.__class__.__name__.lower()] = o()
        return obj

    return f

# def dump(obj):
#     v = JSON_SERIALIZERS
#     x = obj.__class__
#     return JSON_SERIALIZERS[obj.__class__].dump(obj)


def dump(obj):
    if isinstance(obj, (str, int)):
        return obj
    elif isinstance(obj, list):
        return [dump(o) for o in obj]
    elif isinstance(obj, dict):
        if "type" in obj:
            raise ValueError("Error: 'type' in obj %s" % obj)
        return {k: dump(v) for k, v in obj.items()}
    elif obj is None:
        return None
    else:
        custom_serializer = JSON_CUSTOM_SERIALIZERS.get(obj.__class__)
        if custom_serializer is not None:
            return custom_serializer.dump(obj)
        fields = {k: dump(v) for k, v in obj.__dict__.items()}
        if "type" in fields:
            raise ValueError("Error: 'type' in obj %s" % obj)
        fields["type"] = str(obj.__class__.__name__).lower()
        return fields
        # raise ValueError("Unsupported type %s" % obj)


def load(raw):
    print(raw, type(raw))
    if not JSON_CUSTOM_BASE:
        import inspect
        polar = globals()["p"]
        for name in dir(polar):
            if name.startswith("_"):
                continue
            item = getattr(polar, name)
            argspec = inspect.getfullargspec(item.__init__)
            kwargs = list(set(argspec.args + argspec.kwonlyargs) - set(["self"]))
            other = {}
            JSON_CUSTOM_BASE[item.__name__.lower()] = {
                "class": item,
                "kwargs": kwargs,
                "other": other,
            }

    if isinstance(raw, (str, int)):
        return raw
    elif isinstance(raw, list):
        return [load(o) for o in raw]
    elif raw is None:
        return None
    elif isinstance(raw, dict):
        if "type" not in raw:
            return {k: load(v) for k, v in raw.items()}

        custom_serializer = JSON_CUSTOM_SERIALIZERS_BY_NAME.get(raw["type"])
        if custom_serializer is not None:
            return custom_serializer.load(raw)

        if not raw.get("type"):
            raise ValueError("No type in %s" % raw)

        if raw["type"] not in JSON_CUSTOM_BASE:
            print(raw)

        base_serializer = JSON_CUSTOM_BASE[raw["type"]]

        kwargs = {k: load(raw[k]) for k in base_serializer["kwargs"] if k in raw}
        instance = base_serializer["class"](**kwargs)

        for k, v in instance.__dict__.items():
            if k in kwargs:
                continue

            if k not in raw:
                continue

            setattr(instance, k, load(raw[k]))

        return instance


@register(p.NameFeature)
class NameFeature:
    def load(self, raw):
        return NameFeature(vocab={}, var=raw["var"])

    def dump(self, obj):
        return {
            "vocab": "custom",
            "type": "namefeature",
            "var": obj.var,
        }

#
# @register(p.Var)
# class Var:
#     def load(self, raw):
#         return NameFeature(vocab={}, var=raw["var"])
#
#     def dump(self, obj):
#         return {
#             "vocab": "custom",
#             "type": "namefeature",
#             "var": obj.var,
#         }
#
#
# @register(p.Flow)
# class FlowSerializer:
#     def load(self, raw):
#         pass
#
#     def dump(self, obj):
#         return {
#             "commands": dump(obj.commands),
#         }
#
#
# @register(list)
# class ListSerializer:
#     def load(self, raw):
#         pass
#
#     def dump(self, obj):
#         return [dump(o) for o in obj]
#
#
# @register(p.Rule)
# class ListSerializer:
#     def load(self, raw):
#         pass
#
#     def dump(self, obj):
#         return {
#             "name": obj.name,
#             "order": obj.order,
#             "flow": dump(obj.flow),
#         }
