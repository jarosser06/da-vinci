Feature: SideCarApplication shares parent application resources

  A SideCarApplication deploys alongside an existing Application, reads its
  global settings to learn shared infrastructure (event bus, exception trap),
  and registers its own subscribers against the parent's bus. Publishing the
  sidecar's event type via the parent bus must invoke the sidecar handler and
  record a SUCCESS response.

  Scenario: Sidecar subscriber processes an event from the parent bus
    Given a deployed Da Vinci application
    And a deployed Da Vinci sidecar application
    When I publish an "it.sidecar.ping" event with marker "side-1"
    Then the event response status is exactly "SUCCESS"
    And no TrappedException is recorded for "sidecar_echo"

  Scenario: A failing sidecar handler is trapped in the parent's exception trap
    Given a deployed Da Vinci application
    And a deployed Da Vinci sidecar application
    When I publish an "it.sidecar.boom" event with marker "side-boom-1"
    Then the event response status is exactly "FAILURE"
    And the response failure_reason equals "sidecar boom: side-boom-1"
    And a TrappedException is recorded for "sidecar_boom"
    And the trapped exception field equals "sidecar boom: side-boom-1"
    And the trapped exception originating event body marker equals "side-boom-1"

  Scenario: Sidecar writes to the parent's ORM table via a granted access request
    Given a deployed Da Vinci application
    And a deployed Da Vinci sidecar application
    When I publish an "it.sidecar.write" event with marker "side-write-1"
    Then the event response status is exactly "SUCCESS"
    And within 120 seconds a parent PersonTable row with person_id "side-write-1" exists
    And the parent PersonTable row tags equal ["sidecar", "write"]
