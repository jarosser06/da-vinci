Feature: REST service over ORM with global settings

  A SimpleRESTService exposes routes that read and write a DynamoDB-backed
  ORM table and round-trips a GlobalSetting. The Function URL is SigV4-signed,
  so this scenario also validates the framework's IAM wiring.

  Scenario: Create then read a Person via the REST service
    Given a deployed Da Vinci application
    When I POST to /people with name "Ada" age 36
    Then the REST response status is exactly 201
    And the REST response body has a "person_id"

  Scenario: Reading a missing person returns 404
    Given a deployed Da Vinci application
    When I GET person "does-not-exist"
    Then the REST response status is exactly 404

  Scenario: Global settings round-trip
    Given a deployed Da Vinci application
    When I GET the greeting setting
    Then the REST response status is exactly 200
    And the REST response body equals {"namespace": "it::config", "key": "greeting", "value": "hello"}
