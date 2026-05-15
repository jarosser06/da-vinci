Feature: Event bus delivers events to subscribers

  The framework's event bus must route a published event to its subscribed
  handler, record a SUCCESS row in EventBusResponses, and leave the
  exception trap empty for the successful handler.

  Scenario: Successful subscriber records a success response
    Given a deployed Da Vinci application
    When I publish an "it.echo" event with marker "abc123"
    Then the event response status is exactly "SUCCESS"
    And the response has no failure_reason
    And the response has no failure_traceback
    And no TrappedException is recorded for "successful_handler"
