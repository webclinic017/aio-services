::: asvc.broker.Broker
    handler: python
    options:
      members:
        - __init__
        - publish
      show_root_heading: true
      show_source: false

::: asvc.service.Service
    handler: python
    options:
      members:
        - __init__
        - subscribe
      show_root_heading: true
      show_source: false

::: asvc.middleware.Middleware
    handler: python
    options:
      show_root_heading: true
      show_source: false

::: asvc.consumer.Consumer
    handler: python
    options:
      members:
        - __init__
        - process
      show_root_heading: true
      show_source: false

::: asvc.consumer.GenericConsumer
    handler: python
    options:
      members:
        - __init__
        - process
      show_root_heading: true
      show_source: false

