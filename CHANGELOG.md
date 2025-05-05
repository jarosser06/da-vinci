Changelog
=========

### 2025.4.20 (Unreleased)
- Add `da_vinci_cdk.constructs.ai.AIInferenceProfile` construct to create inference profiles as discoverable resources
- Allow for recursive loop on event bus services
- Fix Lambda x86_64 architecture usage
- Add support for initializing an empty ObjectBody
- Fix ORM client update method to use proper DynamoDB Key names
- Add support for regex validation of immutable objects
- Add support for conditional required attributes in immutable object
- Add support for service discovery backed by DynamoDB
- Rename Da Vinci Tables by prepending `da_vinci`
- (**Potentially Breaking**) Remove global_setting toggle, global setting is now required
- (**Potentially Breaking**) Remove `__init__.py` from ORM, Object classes can be accessed from client import `da_vinci.core.orm.client`

### 2024.12.7 (Latest)
- Fix Event object `next_event()` bug where it wasn't referencing the `callback_event_type_on_failure` attribute correctly

### 2024.12.6
- Update Immutable object `get()` to support returning `default_return` when attr is found but value is None
- Update Immutable object Unknown loader to support arbitrary object identification
- Update Immutable object to support secret masking/unmasking

### 2024.12.5
- Fix Table Object to_dict bug for SET types
- Add support for failure callbacks in the event system
- Fix Immutable object _load when object and list attributes are None
- Add `DaVinciObjectEncoder` class to support JSON encoding of commonly used da_vinci objects
- Update Event Bus Response statuses to align more closely with actual status

### 2024.12.4
- Fix event management bug caused by response_id passing

### 2024.12.3
- Skip event_bus attribute validation for objects when there is no schema provided (App)
- Add support for converting nested object bodies when parent object body is converted to a dict
- Fix event bus object mismatched type exception message
- Simplify event bus object schema class
- Fix event bus object body value reference bug
- Add new() method to event bus `ObjectBody` that supports creating a schemaless copy with optional additions
- Support Python native iteration as well as others that enable the `ObjectBody` to operate similar to a native Dict
- Add support for tracking all requests that route through, whether they get a response from runners or not

### 2024.12.2
- Add update support to DynamoDB Item CDK construct (Infra)

### 2024.12.1
- Organize framework stacks into tables vs services (Infra)
- Standardize application feature toggle names (Infra)
- Support event bus access toggle for event bus function construct (App)
- Support calculating defaults for `function_name` attributes in exception trap and event bus wrappers (App)
- Support additional attributes to enable more control over paginated requests in ORM (App)
- Add support for `callback_event_type` attribute with event bus wrapper (App)
- Consolidate settings object names to always identify as global (App)
- Make `raise_on_failure` flag for rest client base to allow author ability to handle < 200 > elsewhere (App)
- Cleaned up unused imports (App, Infra)
- Add ObjectBodySchema validation check method (App)
- Event object now stores the event body object as an `ObjectBody` (App)

### 2.1.1
- Da Vinci before the version change
