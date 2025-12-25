Feature: PostgreSQL Dynamic Secrets Integration
  As a security automation system
  I want to verify that Vault correctly creates users in PostgreSQL
  And that these users can actually log in.

  Scenario: Verify dynamic user creation and database access
    Given Vault is running and the database engine is enabled
    When I request a new credential for the "readonly-role"
    Then Vault should return a valid database username
    And I should be able to connect to "postgres-db" using these credentials