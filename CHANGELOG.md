Changelog
=========

### 2024.12.2 (Latest)
- Add update support to DynamoDB Item CDK construct

### 2024.12.1
- Organize framework stacks into tables vs services (Infra)
- Standardize application feature toggle names (Infra)
- Support event bus access toggle for event bus function construct (App)
- Support calculating defaults for `function_name` attributes in exception trap and event bus wrappers (App)
- Support additional attributes to enable more control over paginated requests in ORM (App)
- Add support for `callback_event_type` attribute with event bus wrapper (App)
- Consolidate settings object names to always identify as global (App)
- Make `raise_on_failure` flag for rest client base to allow author ability to handle < 200 > elsewhere (App)
- Cleaned up unused imports (App, Inra)
- Add ObjectBodySchema validation check method (App)
- Event object now stores the event body object as an `ObjectBody` (App)

### 2.1.1
- Da Vinci before the version change
