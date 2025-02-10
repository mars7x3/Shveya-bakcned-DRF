def serialize_instance(instance, fields):
    if not instance:
        return None
    return {field: getattr(instance, field, None) for field in fields}
