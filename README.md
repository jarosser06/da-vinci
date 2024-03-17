Da Vinci
========
A framework for rapidly developing Python-based AWS Cloud Native applications.

Da Vinci is ideal for projects that require a low-bootstrap cost but require
best-practices for rapidly developed software, internal IT and Intelligent
Business Automation as examples.

For the application deployment and infrastructure management, Da Vinci is purely
CDK under the hood. It utilitzes a few techniques to manage stacks under a single
umbrella without some of the typical pitfalls that come with CloudFormation dependencies.

Currently, I do not have a lot of time to devote to documenting this library, the best place to start is reviewing the
existing framework stacks located in the CDK library.

The framework is split into two libraries:

- `da_vinci` - This is the core library that will be utilized to develop the applcation business logic.
- `da_vinci-cdk` - This is the CDK library that would be utilized to declare the application and AWS resource management.

Example Da Vinci CDK Application
---------------------------------

```python
from da_vinci_cdk.application

env = 'prototype'

app = Application(
    app_name='my_app',
    install_id=f'rosser-{env}',
)

app.synth()
```

What's Included
---------------
- Centralized exception handling - Optional service is created as part of the application deployment. Once the exception trap is deployed, simply wrapping functions with the appropriate decorator allows all caught exceptions to be sent to a centralized place.
- Built-in Event Bus - When an application calls for simple event subscriptions to handle application logic, the event bus works well to facilitate calling the subscribed lambda functions. It also includes a response handler to track event responses as they make their way through the system.