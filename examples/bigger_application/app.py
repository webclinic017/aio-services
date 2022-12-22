from asvc import ServiceRunner
from .broker import broker

from module_a.service import service_a

app = ServiceRunner(broker=broker, services=[service_a])

if __name__ == "__main__":
    app.run()
