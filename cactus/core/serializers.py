from rest_framework import serializers


class BaseWithNotIncludeField(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        # Pega os campos que foram especificados.
        not_fields = kwargs.pop("not_include_fields", None)
        super(BaseWithNotIncludeField, self).__init__(*args, **kwargs)

        if not_fields:
            # Remove todos os campos que estão na lista especificada.
            for field_name in set(not_fields):
                self.fields.pop(field_name)
