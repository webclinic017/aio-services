::: aio_services.broker.Broker
    handler: python
    options:
      members:
        - __init__
        - publish
      show_root_heading: true
      show_source: false

::: aio_services.service.Service
    handler: python
    options:
      members:
        - __init__
        - subscribe
      show_root_heading: true
      show_source: false

::: aio_services.middleware.Middleware
    handler: python
    options:
      show_root_heading: true
      show_source: false

::: aio_services.consumer.Consumer
    handler: python
    options:
      members:
        - __init__
      show_root_heading: true
      show_source: false

::: aio_services.consumer.GenericConsumer
    handler: python
    options:
      members:
        - __init__
        - process
      show_root_heading: true
      show_source: false

