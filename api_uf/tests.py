from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import UF  # Para criar dados de teste, se necessário, ou verificar o BD
from bo.uf.uf import UfBO  # Para interagir com a camada de BO, se necessário para setup/teardown


class UFAPITests(APITestCase):
    def setUp(self):
        # Limpar a tabela UF usando BO antes de cada teste para garantir isolamento
        # Isso é importante porque estamos usando SQL puro e não o ORM do Django para testes.
        # Se usássemos o ORM, o Django cuidaria do rollback do banco de dados de teste.
        # Com SQL puro, precisamos garantir um estado limpo.
        self.bo = UfBO()

        # Uma forma de limpar: buscar todos e deletar um por um.
        # Em um cenário real com muitos dados, pode ser lento.
        # Alternativamente, poderia truncar a tabela se o SGBD e permissões permitirem.
        all_ufs_data = self.bo.get_all_ufs()
        for uf_data in all_ufs_data:
            self.bo.delete_uf(uf_data['id'])

        # Criar algumas UFs de exemplo para testes de GET, PUT, DELETE
        self.uf1_data = self.bo.create_uf(nome="Paraná", sigla="PR", codigo_ibge=41)
        self.uf2_data = self.bo.create_uf(nome="Santa Catarina", sigla="SC", codigo_ibge=42)

    def test_create_uf_success(self):
        """Garante que podemos criar uma nova UF."""
        url = reverse('uf-list')  # 'uf-list' é o nome padrão para a ação 'list' e 'create' do ViewSet
        data = {'nome': 'Sao Paulo', 'sigla': 'SP', 'codigo_ibge': 35}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nome'], 'Sao Paulo')
        self.assertEqual(response.data['sigla'], 'SP')
        self.assertEqual(response.data['codigo_ibge'], 35)
        self.assertTrue('id' in response.data)

        # Verificar no banco através do BO
        created_uf_from_bo = self.bo.get_uf_by_id(response.data['id'])
        self.assertIsNotNone(created_uf_from_bo)
        self.assertEqual(created_uf_from_bo['nome'], 'Sao Paulo')

    def test_create_uf_invalid_sigla_length(self):
        """Testa a criação de UF com sigla inválida (comprimento)."""
        url = reverse('uf-list')
        data = {'nome': 'Rio de Janeiro', 'sigla': 'RJJ', 'codigo_ibge': 33}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('sigla', response.data)

    def test_create_uf_invalid_sigla_format(self):
        """Testa a criação de UF com sigla inválida (formato)."""
        url = reverse('uf-list')
        data = {'nome': 'Rio de Janeiro', 'sigla': 'R1', 'codigo_ibge': 33}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('sigla', response.data)
        self.assertEqual(str(response.data['sigla'][0]), "Sigla deve conter apenas 2 letras maiúsculas.")

    def test_create_uf_missing_field(self):
        """Testa a criação de UF com campo faltando."""
        url = reverse('uf-list')
        data = {'nome': 'Acre', 'sigla': 'AC'}  # codigo_ibge faltando
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('codigo_ibge', response.data)

    def test_list_ufs(self):
        """Garante que podemos listar UFs."""
        url = reverse('uf-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Baseado no setUp
        self.assertEqual(response.data[0]['nome'], self.uf1_data['nome'])  # Assumindo ordenação por nome
        self.assertEqual(response.data[1]['nome'], self.uf2_data['nome'])

    def test_retrieve_uf(self):
        """Garante que podemos buscar uma UF específica."""
        url = reverse('uf-detail', kwargs={'pk': self.uf1_data['id']})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nome'], self.uf1_data['nome'])

    def test_retrieve_uf_not_found(self):
        """Testa buscar uma UF inexistente."""
        url = reverse('uf-detail', kwargs={'pk': 999})  # ID improvável
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_uf(self):
        """Garante que podemos atualizar uma UF."""
        url = reverse('uf-detail', kwargs={'pk': self.uf1_data['id']})
        updated_data = {'nome': 'Parana Alterado', 'sigla': 'PR', 'codigo_ibge': 410}
        response = self.client.put(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nome'], 'Parana Alterado')
        self.assertEqual(response.data['codigo_ibge'], 410)

        # Verificar no banco através do BO
        uf_from_bo = self.bo.get_uf_by_id(self.uf1_data['id'])
        self.assertEqual(uf_from_bo['nome'], 'Parana Alterado')

    def test_partial_update_uf(self):
        """Garante que podemos atualizar parcialmente uma UF."""
        url = reverse('uf-detail', kwargs={'pk': self.uf2_data['id']})
        partial_data = {'nome': 'Santa Catarina Alterado'}
        response = self.client.patch(url, partial_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nome'], 'Santa Catarina Alterado')
        self.assertEqual(response.data['sigla'], self.uf2_data['sigla'])  # Sigla não deve mudar

        # Verificar no banco através do BO
        uf_from_bo = self.bo.get_uf_by_id(self.uf2_data['id'])
        self.assertEqual(uf_from_bo['nome'], 'Santa Catarina Alterado')

    def test_delete_uf(self):
        """Garante que podemos deletar uma UF."""
        uf_to_delete_data = self.bo.create_uf(nome="Para Deletar", sigla="PD", codigo_ibge=99)
        self.assertIsNotNone(uf_to_delete_data, "Falha ao criar UF para teste de deleção.")

        url = reverse('uf-detail', kwargs={'pk': uf_to_delete_data['id']})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verificar no banco através do BO
        uf_from_bo = self.bo.get_uf_by_id(uf_to_delete_data['id'])
        self.assertIsNone(uf_from_bo)

    def test_delete_uf_not_found(self):
        """Testa deletar uma UF inexistente."""
        url = reverse('uf-detail', kwargs={'pk': 999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
