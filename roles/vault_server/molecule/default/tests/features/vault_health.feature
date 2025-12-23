Feature: Vault Server Health and Security
  # Description: Critical infrastructure requirements to ensure Vault is 
  # properly installed and ready to handle secrets.

  Scenario: Verify that the Vault service is operational and configured
    Given the Vault container is running
    When I check the Vault file system status
    Then the "vault" binary should be installed in the PATH
    And the service should be listening on port 8200