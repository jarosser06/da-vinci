"""REST service for the integration suite.

Exposes:
  * POST /people           — create a PersonTable row (responds 201)
  * GET  /people/get       — fetch a person by id (responds 200 or 404)
  * GET  /settings/greeting — round-trip the seeded GlobalSetting (responds 200)

The framework's SimpleRESTServiceBase does exact-match path routing; path
parameters are passed via query/body. The test invokes via ``GET
/people/get?person_id=xyz`` rather than path variables.
"""

from handlers.shared.person import PersonTableClient, PersonTableObject

from da_vinci.core.global_settings import setting_value
from da_vinci.core.rest_service_base import (
    NotFoundResponse,
    Route,
    SimpleRESTServiceBase,
)
from da_vinci.exception_trap.client import ExceptionReporter


class PeopleService(SimpleRESTServiceBase):
    def __init__(self) -> None:
        self.people = PersonTableClient()

        super().__init__(
            routes=[
                Route(
                    handler=self.create_person,
                    method="POST",
                    path="/people",
                    required_arguments=["name"],
                ),
                Route(
                    handler=self.get_person,
                    method="GET",
                    path="/people/get",
                    required_arguments=["person_id"],
                ),
                Route(
                    handler=self.get_greeting,
                    method="GET",
                    path="/settings/greeting",
                ),
            ],
            exception_reporter=ExceptionReporter(),
            exception_function_name="it_people_rest",
        )

    def create_person(self, **kwargs):
        person = PersonTableObject(**kwargs)

        self.people.put(person)

        return self.respond(body=person.to_dict(), status_code=201)

    def get_person(self, person_id: str):
        person = self.people.get(person_id=person_id)

        if person is None:
            return NotFoundResponse(f"person_id {person_id} not found").to_dict()

        return self.respond(body=person.to_dict(), status_code=200)

    def get_greeting(self, **kwargs: object) -> dict:
        del kwargs

        value = setting_value(namespace="it::config", setting_key="greeting")

        return self.respond(
            body={"namespace": "it::config", "key": "greeting", "value": value},
            status_code=200,
        )


def handler(event: dict, context: object) -> dict:
    del context

    return PeopleService().handle(event=event)
