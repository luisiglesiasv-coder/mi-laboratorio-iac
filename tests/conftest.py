# tests/conftest.py
import os

# Definimos el directorio base de las features.
# La ruta debe ser relativa desde donde se ejecuta pytest (tests/)
# Usamos os.path.join para asegurar la compatibilidad del sistema operativo.
# En este caso, le decimos que la base de las features está en el directorio actual (features)
pytest_bdd_features_base_dir = os.path.join(os.path.dirname(__file__), 'features')


import pytest

# Definimos una clase simple para guardar datos
class Context:
    def __init__(self):
        # Aquí puedes inicializar valores por defecto si quieres
        self.data = {}

# Creamos la fixture que Pytest inyectará cuando alguien pida 'context'
@pytest.fixture
def context():
    """
    Retorna una instancia de Context nueva para cada escenario.
    Esto asegura que los datos de una prueba no contaminen a la otra.
    """
    return Context()
