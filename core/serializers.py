from rest_framework import serializers


class SCSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        remove_field = kwargs.pop("remove_field", None)
        super(SCSerializer, self).__init__(*args, **kwargs)

        if remove_field:
            # Remove todos os campos que estão na lista especificada.
            for field_name in remove_field:
                self.fields.pop(field_name)

        self.internal_value_methods = {
            key: getattr(self, f"internal_value_for_{key}", None) for key in self.fields
        }

        self.representation_methods = {
            key: getattr(self, f"representation_for_{key}", None) for key in self.fields
        }

    def to_internal_value(self, data):
        data_copy = data.copy()

        for key, value in data_copy.items():
            function = self.internal_value_methods.get(key)

            if function and callable(function):
                try:
                    data_copy[key] = function(value)
                except Exception as e:
                    raise serializers.ValidationError(
                        f"Erro ao processar {key}: {str(e)}"
                    )

        return super().to_internal_value(data_copy)

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        for key, value in representation.items():
            function = self.representation_methods.get(key)

            if function and callable(function):
                try:
                    representation[key] = function(value)
                except Exception as e:
                    raise serializers.ValidationError(
                        f"Erro ao processar {key}: {str(e)}"
                    )

        return representation
