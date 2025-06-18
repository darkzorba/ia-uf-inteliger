from bo.base.sql import SQLClass
import logging

logger = logging.getLogger(__name__)

class UfBO(SQLClass):
    def __init__(self):
        super().__init__()
        self.table_name = "uf" # Nome da tabela conforme definido no modelo

    def create_uf(self, nome, sigla, codigo_ibge):
        """Cria uma nova UF."""
        query = f"""
            INSERT INTO {self.table_name} (nome, sigla, codigo_ibge)
            VALUES (%s, %s, %s)
            RETURNING id, nome, sigla, codigo_ibge;
        """
        params = (nome, sigla, codigo_ibge)
        try:
            logger.info(f"Attempting to create UF with nome='{nome}', sigla='{sigla}', codigo_ibge={codigo_ibge}")
            # Usaremos execute_select com fetch_one=True para capturar o RETURNING como um dict
            created_uf_tuple = self._execute_query(query, params, fetch_one=True, commit=True)
            if created_uf_tuple:
                 # Convertendo a tupla para dicionário
                columns = ['id', 'nome', 'sigla', 'codigo_ibge']
                created_uf_dict = dict(zip(columns, created_uf_tuple))
                logger.info(f"UF created successfully: {created_uf_dict}")
                return created_uf_dict
            logger.warning("UF creation did not return any data.")
            return None
        except Exception as e:
            logger.error(f"Failed to create UF: {e}")
            raise

    def get_all_ufs(self):
        """Busca todas as UFs."""
        query = f"SELECT id, nome, sigla, codigo_ibge FROM {self.table_name} ORDER BY nome;"
        try:
            logger.info("Fetching all UFs")
            ufs = self.execute_select(query)
            logger.info(f"Found {len(ufs)} UFs.")
            return ufs
        except Exception as e:
            logger.error(f"Failed to fetch all UFs: {e}")
            raise

    def get_uf_by_id(self, uf_id):
        """Busca uma UF pelo ID."""
        query = f"SELECT id, nome, sigla, codigo_ibge FROM {self.table_name} WHERE id = %s;"
        params = (uf_id,)
        try:
            logger.info(f"Fetching UF with id={uf_id}")
            uf = self.execute_select(query, params, fetch_one=True)
            if uf:
                logger.info(f"UF found: {uf}")
            else:
                logger.warning(f"UF with id={uf_id} not found.")
            return uf
        except Exception as e:
            logger.error(f"Failed to fetch UF by id={uf_id}: {e}")
            raise

    def update_uf(self, uf_id, nome=None, sigla=None, codigo_ibge=None):
        """Atualiza uma UF existente."""
        fields_to_update = []
        params = []

        if nome is not None:
            fields_to_update.append("nome = %s")
            params.append(nome)
        if sigla is not None:
            fields_to_update.append("sigla = %s")
            params.append(sigla)
        if codigo_ibge is not None:
            fields_to_update.append("codigo_ibge = %s")
            params.append(codigo_ibge)

        if not fields_to_update:
            logger.warning("No fields provided for UF update.")
            return 0 # Nenhuma alteração

        params.append(uf_id)
        query = f"""
            UPDATE {self.table_name}
            SET {', '.join(fields_to_update)}
            WHERE id = %s;
        """
        try:
            logger.info(f"Attempting to update UF with id={uf_id}. New data: nome='{nome}', sigla='{sigla}', codigo_ibge={codigo_ibge}")
            affected_rows = self.execute_update(query, tuple(params))
            if affected_rows > 0:
                logger.info(f"UF with id={uf_id} updated successfully. {affected_rows} row(s) affected.")
            else:
                logger.warning(f"UF with id={uf_id} not found or no changes made during update.")
            return affected_rows
        except Exception as e:
            logger.error(f"Failed to update UF with id={uf_id}: {e}")
            raise

    def delete_uf(self, uf_id):
        """Deleta uma UF."""
        query = f"DELETE FROM {self.table_name} WHERE id = %s;"
        params = (uf_id,)
        try:
            logger.info(f"Attempting to delete UF with id={uf_id}")
            affected_rows = self.execute_delete(query, params)
            if affected_rows > 0:
                logger.info(f"UF with id={uf_id} deleted successfully. {affected_rows} row(s) affected.")
            else:
                logger.warning(f"UF with id={uf_id} not found for deletion.")
            return affected_rows
        except Exception as e:
            logger.error(f"Failed to delete UF with id={uf_id}: {e}")
            raise