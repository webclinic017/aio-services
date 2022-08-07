def test_add_middleware(broker, middleware):
    broker.add_middleware(middleware)
    assert middleware in broker.middlewares
