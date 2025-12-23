import pytest
import testinfra

@pytest.fixture(scope="module")
def host(request):
    """
    This fixture overrides the default Testinfra fixture to ensure it 
    returns the correct host provided by Molecule, even when using Pytest-BDD.
    The 'module' scope ensures the connection is reused for all tests in this file.
    """
    
    # Check if Pytest has the 'param' attribute which contains the host connection string
    if hasattr(request, "param"):
        return testinfra.get_host(request.param)
    
    # Fallback logic: If Molecule/Pytest-BDD fails to pass the parameter, 
    # we manually point to the Docker container defined in molecule.yml.
    # The string format is 'docker://<container_name>'
    return testinfra.get_host("docker://vault-unit-test")