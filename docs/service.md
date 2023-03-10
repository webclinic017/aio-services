## Service

`Service` object is the main object in your app. It is a logical group of consumers which it binds to the broker.

::: asvc.service.Service
    handler: python
    options:
      members:
        - __init__
        - subscribe
      show_root_heading: true
      show_source: false


## Service Runner

Service runner class is a service container, responsible to run one or more services, as a standalone
program. If you want to run only one service, the `ServiceRunner` instance will be created under the hood.

::: asvc.runner.ServiceRunner
    handler: python
    options:
      members:
        - __init__
        - run
      show_root_heading: true
      show_source: false