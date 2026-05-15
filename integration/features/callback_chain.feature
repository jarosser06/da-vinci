Feature: Callback event chains link events via previous_event_id

  A handler that returns a value and is wrapped with handle_callbacks=True
  must trigger a follow-up event whose previous_event_id points back to the
  originating event. The second handler proves receipt by writing to
  PersonTable.

  Scenario: First-stage handler triggers second-stage handler
    Given a deployed Da Vinci application
    When I publish an "it.chain.start" event with marker "chained-1" and callback "it.chain.end"
    Then the event response status is exactly "SUCCESS"
    And within 90 seconds a PersonTable row with person_id "chained-1" exists
    And the PersonTable row tags equal ["chain", "second"]
