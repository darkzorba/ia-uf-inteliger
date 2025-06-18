from rest_framework import viewsets, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UFSerializer
from bo.uf.uf import UfBO  # Importando nossa classe de lógica de negócios
import logging

logger = logging.getLogger(__name__)

# --- Schemas Reutilizáveis para Respostas ---
uf_schema = UFSerializer # Usaremos o próprio serializer para o schema de sucesso

error_400_validation_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    description="Erro de validação nos dados enviados.",
    properties={
        'field_name': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(type=openapi.TYPE_STRING),
            description="Lista de erros para o campo específico."
        )
    },
    example={'sigla': ['Este campo deve ter exatamente 2 caracteres.', 'Sigla deve conter apenas 2 letras maiúsculas.']}
)

error_404_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    description="Recurso não encontrado.",
    properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description="Mensagem de erro detalhando o recurso não encontrado.")},
    example={'error': 'UF não encontrada.'}
)

error_500_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    description="Erro interno do servidor.",
    properties={'error': openapi.Schema(type=openapi.TYPE_STRING, description="Mensagem de erro genérica ou detalhe do erro interno.")},
    example={'error': 'Ocorreu um erro inesperado ao processar a requisição.'}
)

# --- Parâmetro de Path Reutilizável ---
pk_param_docs = openapi.Parameter(
    'pk',
    openapi.IN_PATH,
    description="ID (Chave Primária) da Unidade Federativa.",
    type=openapi.TYPE_INTEGER,
    required=True
)

class UFViewSet(viewsets.ViewSet):
    """
    API endpoint para gerenciar Unidades Federativas (UFs).
    Permite criar, listar, detalhar, atualizar e excluir UFs.
    A lógica de negócios é manipulada pela camada UfBO utilizando SQL puro.
    """
    bo = UfBO()

    @swagger_auto_schema(
        operation_summary="Listar todas as UFs",
        operation_description="Retorna uma lista de todas as Unidades Federativas cadastradas no sistema.",
        responses={
            status.HTTP_200_OK: UFSerializer(many=True, help_text="Lista de UFs retornada com sucesso."),
            status.HTTP_500_INTERNAL_SERVER_ERROR: error_500_schema
        },
        tags=['UFs']
    )
    def list(self, request):
        """Lista todas as UFs."""
        try:
            ufs = self.bo.get_all_ufs()
            serializer = UFSerializer(ufs, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"API Error listing UFs: {e}")
            return Response({"error": "Erro ao listar UFs."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Criar uma nova UF",
        operation_description="Cria uma nova Unidade Federativa com os dados fornecidos.",
        request_body=UFSerializer,
        responses={
            status.HTTP_201_CREATED: UFSerializer(help_text="UF criada com sucesso."),
            status.HTTP_400_BAD_REQUEST: error_400_validation_schema,
            status.HTTP_500_INTERNAL_SERVER_ERROR: error_500_schema
        },
        tags=['UFs']
    )
    def create(self, request):
        """Cria uma nova UF."""
        serializer = UFSerializer(data=request.data)
        if serializer.is_valid():
            try:
                data = serializer.validated_data
                created_uf_dict = self.bo.create_uf(
                    nome=data['nome'],
                    sigla=data['sigla'],
                    codigo_ibge=data['codigo_ibge']
                )
                if created_uf_dict:
                    response_serializer = UFSerializer(created_uf_dict)
                    return Response(response_serializer.data, status=status.HTTP_201_CREATED)
                else:
                    logger.error("API Error: UF creation in BO did not return data.")
                    return Response({"error": "Erro ao criar UF, não houve retorno do BO."},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e: # Idealmente, capturar exceções mais específicas do BO (ex: UniqueConstraintError)
                logger.error(f"API Error creating UF: {e}")
                # Verificar se o erro é de violação de constraint (ex: psycopg.errors.UniqueViolation)
                # e retornar um 400 ou 409 mais específico.
                # Por ora, mantendo genérico para 500.
                return Response({"error": f"Erro interno ao criar UF: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Detalhar uma UF específica",
        operation_description="Retorna os detalhes de uma Unidade Federativa específica, identificada pelo seu ID.",
        manual_parameters=[pk_param_docs],
        responses={
            status.HTTP_200_OK: UFSerializer(help_text="Detalhes da UF retornados com sucesso."),
            status.HTTP_404_NOT_FOUND: error_404_schema,
            status.HTTP_500_INTERNAL_SERVER_ERROR: error_500_schema
        },
        tags=['UFs']
    )
    def retrieve(self, request, pk=None):
        """Busca uma UF específica pelo ID (pk)."""
        try:
            uf = self.bo.get_uf_by_id(pk)
            if uf:
                serializer = UFSerializer(uf)
                return Response(serializer.data)
            return Response({"error": "UF não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"API Error retrieving UF {pk}: {e}")
            return Response({"error": "Erro ao buscar UF."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Atualizar uma UF (PUT)",
        operation_description="Atualiza todos os campos de uma Unidade Federativa existente. Todos os campos são obrigatórios.",
        manual_parameters=[pk_param_docs],
        request_body=UFSerializer,
        responses={
            status.HTTP_200_OK: UFSerializer(help_text="UF atualizada com sucesso."),
            status.HTTP_400_BAD_REQUEST: error_400_validation_schema,
            status.HTTP_404_NOT_FOUND: error_404_schema,
            status.HTTP_500_INTERNAL_SERVER_ERROR: error_500_schema
        },
        tags=['UFs']
    )
    def update(self, request, pk=None):
        """Atualiza uma UF existente."""
        serializer = UFSerializer(data=request.data)
        if serializer.is_valid():
            try:
                data = serializer.validated_data
                affected_rows = self.bo.update_uf(
                    uf_id=pk,
                    nome=data.get('nome'),
                    sigla=data.get('sigla'),
                    codigo_ibge=data.get('codigo_ibge')
                )
                if affected_rows > 0:
                    updated_uf = self.bo.get_uf_by_id(pk)
                    if updated_uf:
                        response_serializer = UFSerializer(updated_uf)
                        return Response(response_serializer.data)
                    else:
                        logger.error(f"API Error: UF {pk} updated but could not be retrieved.")
                        return Response({"error": "UF atualizada, mas não pôde ser recuperada."},
                                        status=status.HTTP_200_OK) # Ou um 500 se isso for crítico
                elif affected_rows == 0:
                    # Verificar se a UF existe antes de dizer que não foi alterada
                    # Se self.bo.get_uf_by_id(pk) retornar None aqui, então é 404.
                    # Se existir mas não houve alteração (dados iguais), pode ser um 200 com a UF original ou 304 Not Modified.
                    # Por simplicidade, mantendo o 404 se affected_rows for 0.
                    return Response({"error": "UF não encontrada ou nenhum dado alterado."},
                                    status=status.HTTP_404_NOT_FOUND)
                # else: # O BO.update_uf retorna rowcount, não deveria ser < 0
                #     return Response({"error": "Erro ao atualizar UF."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            except Exception as e:
                logger.error(f"API Error updating UF {pk}: {e}")
                return Response({"error": f"Erro interno ao atualizar UF: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Atualizar parcialmente uma UF (PATCH)",
        operation_description="Atualiza um ou mais campos de uma Unidade Federativa existente. Apenas os campos fornecidos serão alterados.",
        manual_parameters=[pk_param_docs],
        request_body=UFSerializer(partial=True, help_text="Apenas os campos a serem atualizados precisam ser enviados."),
        responses={
            status.HTTP_200_OK: UFSerializer(help_text="UF atualizada parcialmente com sucesso."),
            status.HTTP_400_BAD_REQUEST: error_400_validation_schema,
            status.HTTP_404_NOT_FOUND: error_404_schema,
            status.HTTP_500_INTERNAL_SERVER_ERROR: error_500_schema
        },
        tags=['UFs']
    )
    def partial_update(self, request, pk=None):
        """Atualiza parcialmente uma UF existente (PATCH)."""
        serializer = UFSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            try:
                data = serializer.validated_data
                affected_rows = self.bo.update_uf(
                    uf_id=pk,
                    nome=data.get('nome'),
                    sigla=data.get('sigla'),
                    codigo_ibge=data.get('codigo_ibge')
                )
                if affected_rows > 0:
                    updated_uf = self.bo.get_uf_by_id(pk)
                    if updated_uf:
                        response_serializer = UFSerializer(updated_uf)
                        return Response(response_serializer.data)
                    else:
                        logger.error(f"API Error: UF {pk} partially updated but could not be retrieved.")
                        return Response({"error": "UF atualizada parcialmente, mas não pôde ser recuperada."},
                                        status=status.HTTP_200_OK) # Ou um 500
                elif affected_rows == 0:
                    return Response({"error": "UF não encontrada ou nenhum dado alterado."},
                                    status=status.HTTP_404_NOT_FOUND)
                # else:
                #     return Response({"error": "Erro ao atualizar UF parcialmente."},
                #                     status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            except Exception as e:
                logger.error(f"API Error partially updating UF {pk}: {e}")
                return Response({"error": f"Erro interno ao atualizar UF parcialmente: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Excluir uma UF",
        operation_description="Exclui permanentemente uma Unidade Federativa do sistema, identificada pelo seu ID.",
        manual_parameters=[pk_param_docs],
        responses={
            status.HTTP_204_NO_CONTENT: openapi.Response(description="UF excluída com sucesso. Nenhum conteúdo retornado."),
            status.HTTP_404_NOT_FOUND: error_404_schema,
            status.HTTP_500_INTERNAL_SERVER_ERROR: error_500_schema
        },
        tags=['UFs']
    )
    def destroy(self, request, pk=None):
        """Deleta uma UF."""
        try:
            affected_rows = self.bo.delete_uf(pk)
            if affected_rows > 0:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({"error": "UF não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"API Error deleting UF {pk}: {e}")
            return Response({"error": "Erro ao deletar UF."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
