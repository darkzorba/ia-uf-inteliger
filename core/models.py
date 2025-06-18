from django.db import models

class UF(models.Model):
    nome = models.CharField(max_length=100, unique=True, blank=False, null=False)
    sigla = models.CharField(max_length=2, unique=True, blank=False, null=False)
    codigo_ibge = models.IntegerField(unique=True, blank=False, null=False)
    # Django adiciona um campo 'id' AutoField automaticamente como chave primária

    def __str__(self):
        return f"{self.nome} ({self.sigla})"

    class Meta:
        verbose_name = "Unidade Federativa"
        verbose_name_plural = "Unidades Federativas"
        db_table = 'uf' # Especificando o nome da tabela como 'uf'