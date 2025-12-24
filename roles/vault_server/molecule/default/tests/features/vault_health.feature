Feature: Vault Full Lifecycle and Provisioning
  As a DevOps Engineer
  I want to verify that Vault is correctly installed, initialized, and provisioned
  So that the infrastructure is ready for the CI-Runner.

  Scenario: Verify system health and service availability
    Given the Vault container is running
    When I check the Vault system status
    Then the "vault" binary should be installed in the PATH
    And the service should be listening on port 8200

  Scenario: Verify security provisioning (AppRole and Policies)
    Given the Vault server is initialized and unsealed
    When I query the enabled authentication methods
    Then the "approle/" method should be enabled
    And the policy "ci-runner-policy" should be present in Vault