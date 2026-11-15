from app.registry.models import ServiceDescriptor, ServiceRegistration


class DuplicateServiceError(Exception):
    pass


class ServiceRegistry:
    def __init__(self) -> None:
        self._services: dict[str, ServiceDescriptor] = {}

    def register(self, registration: ServiceRegistration) -> ServiceDescriptor:
        if registration.service_name in self._services:
            raise DuplicateServiceError(registration.service_name)

        descriptor = ServiceDescriptor.model_validate(registration.model_dump())
        self._services[descriptor.service_name] = descriptor
        return descriptor

    def list_services(self) -> list[ServiceDescriptor]:
        return [self._services[name] for name in sorted(self._services)]

    def get_service(self, service_name: str) -> ServiceDescriptor | None:
        return self._services.get(service_name)

    def discover(self, capability: str) -> list[ServiceDescriptor]:
        normalized = capability.strip().lower()
        return [
            service
            for service in self.list_services()
            if normalized in service.capabilities
        ]
