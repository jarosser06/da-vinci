Feature: Failing subscribers route exceptions to the trap

  The framework wraps event-bus handlers with a decorator that catches
  exceptions, records a FAILURE response, and forwards the exception to the
  trap. The validation must compare the trapped payload byte-for-byte against
  the body that triggered the failure.

  Scenario: A raising handler records an exact TrappedException
    Given a deployed Da Vinci application
    When I publish an "it.boom" event with marker "xyz789"
    Then the event response status is exactly "FAILURE"
    And the response failure_reason equals "intentional boom: xyz789"
    And a TrappedException is recorded for "failing_handler"
    And the trapped exception field equals "intentional boom: xyz789"
    And the trapped exception originating event body marker equals "xyz789"
