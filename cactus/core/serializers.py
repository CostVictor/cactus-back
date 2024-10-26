from rest_framework import serializers


class SCSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        # Pega os campos que foram especificados.
        not_fields = kwargs.pop("remove_field", None)
        super(SCSerializer, self).__init__(*args, **kwargs)

        if not_fields:
            # Remove todos os campos que estão na lista especificada.
            for field_name in set(not_fields):
                self.fields.pop(field_name)
