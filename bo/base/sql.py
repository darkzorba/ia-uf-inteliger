import psycopg
from django.conf import settings
import logging

# Configuração básica de logging para a SQLClass
logger = logging.getLogger(__name__)


class SQLClass:
    def __init__(self):
        self.db_settings = settings.DATABASES['default']
        self.conn_params = {
            "dbname": self.db_settings['NAME'],
            "user": self.db_settings['USER'],
            "password": self.db_settings['PASSWORD'],
            "host": self.db_settings['HOST'],
            "port": self.db_settings['PORT'],
        }

    def _execute_query(self, query, params=None, fetch_one=False, fetch_all=False, commit=False):
        """
        Executa uma query SQL.
        Retorna o cursor para fetch_one/fetch_all ou o resultado do commit.
        """
        conn = None
        cur = None
        try:
            conn = psycopg.connect(**self.conn_params)
            cur = conn.cursor()
            logger.debug(f"Executing query: {query} with params: {params}")
            cur.execute(query, params)

            if commit:
                conn.commit()
                logger.info("Query committed successfully.")
                # Para INSERT/UPDATE/DELETE, podemos retornar o rowcount ou um ID específico se a query o fizer.
                # Por exemplo, se a query for "INSERT ... RETURNING id", fetch_one=True pegaria o ID.
                if fetch_one and cur.description:  # Verifica se há algo para buscar (ex: RETURNING clause)
                    return cur.fetchone()
                return cur.rowcount  # Número de linhas afetadas

            if fetch_one:
                return cur.fetchone()
            if fetch_all:
                return cur.fetchall()

            return None  # Caso não seja commit nem fetch

        except psycopg.Error as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()  # Garante rollback em caso de erro durante commit
            # Relança a exceção para que a camada superior possa tratá-la ou para debug
            # Em um ambiente de produção, você pode querer tratar isso de forma mais específica.
            raise
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    def _dictfetchone(self, cursor):
        """Retorna uma linha do cursor como um dicionário."""
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [col[0] for col in cursor.description]
        return dict(zip(columns, row))

    def _dictfetchall(self, cursor):
        """Retorna todas as linhas do cursor como uma lista de dicionários."""
        rows = cursor.fetchall()
        if not rows:
            return []
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    def execute_select(self, query, params=None, fetch_one=False):
        """
        Executa uma query SELECT e retorna os resultados como dicionários.
        """
        conn = None
        cur = None
        try:
            conn = psycopg.connect(**self.conn_params)
            cur = conn.cursor()
            logger.debug(f"Executing SELECT query: {query} with params: {params}")
            cur.execute(query, params)

            if fetch_one:
                return self._dictfetchone(cur)
            return self._dictfetchall(cur)

        except psycopg.Error as e:
            logger.error(f"Database error during SELECT: {e}")
            raise
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    def execute_insert(self, query, params=None, returning_id=True):
        """
        Executa uma query INSERT.
        Se returning_id for True, espera-se que a query tenha "RETURNING id".
        """
        try:
            result = self._execute_query(query, params, commit=True, fetch_one=returning_id)
            if returning_id and result:
                return result[0]  # Retorna o ID
            return result  # Retorna rowcount se não houver RETURNING id
        except Exception as e:
            logger.error(f"Error during INSERT operation: {e}")
            raise

    def execute_update(self, query, params=None):
        """Executa uma query UPDATE e retorna o número de linhas afetadas."""
        try:
            return self._execute_query(query, params, commit=True)
        except Exception as e:
            logger.error(f"Error during UPDATE operation: {e}")
            raise

    def execute_delete(self, query, params=None):
        """Executa uma query DELETE e retorna o número de linhas afetadas."""
        try:
            return self._execute_query(query, params, commit=True)
        except Exception as e:
            logger.error(f"Error during DELETE operation: {e}")
            raise