"""Exceptions for the event bus."""


class CircularDependencyError(ValueError):
    def __init__(self, subscription_event_type: str, function_name: str) -> None:
        """
        Raised when a circular dependency is detected.

        Keyword Arguments:
            subscription_event_type (str): The event type that was subscribed to
            function_name (str): The name of the function that subscribed to the event type
        """
        super().__init__(
            f"Function subscription {function_name} cannot subscribe to the self generated event {subscription_event_type}."
        )
