Da Vinci
========
A framework for rapidly developing Python-based AWS Cloud Native applications.

Da Vinci is ideal for projects that require a low-bootstrap cost but require
best-practices for rapidly developed software, internal IT and Intelligent
Business Automation as examples.

For the application deployment and infrastructure management, Da Vinci is purely
CDK under the hood. It utilitzes a few techniques to manage stacks under a single
umbrella without some of the typical pitfalls that come with CloudFormation dependencies.


Example Application
-------------------

```python
env = 'prototype'

app = Application(
    app_name='my_app',
    install_id=f'rosser-{env}',
)


app.synth()
```
