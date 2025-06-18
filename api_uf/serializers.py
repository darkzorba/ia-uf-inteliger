from rest_framework import serializers
# O modelo UF está em core.models, não em api_uf.models
# from .models import UF # Remova esta linha se api_uf/models.py não existir ou não definir UF
from core.models import UF # Importe UF de core.models

class UFSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    nome = serializers.CharField(max_length=100)
    sigla = serializers.CharField(max_length=2, min_length=2) # Validação de tamanho
    codigo_ibge = serializers.IntegerField()

    def validate_sigla(self, value):
        """
        Validação customizada para garantir que a sigla seja composta por 2 letras maiúsculas.
        """
        if not value.isalpha() or not value.isupper():
            raise serializers.ValidationError("Sigla deve conter apenas 2 letras maiúsculas.")
        return value

    # Não precisamos de create() e update() aqui se a ViewSet for lidar com a lógica de BO.
    # Se a ViewSet usasse o ORM diretamente com ModelSerializer, eles seriam úteis.
    # Como estamos usando uma camada BO com SQL puro, a ViewSet chamará os métodos da BO.