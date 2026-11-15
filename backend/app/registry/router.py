from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status

from app.registry.models import ServiceDescriptor, ServiceRegistration
from app.registry.repository import DuplicateServiceError, ServiceRegistry

router = APIRouter(prefix="/api/registry", tags=["registry"])


def get_registry(request: Request) -> ServiceRegistry:
    return request.app.state.service_registry


RegistryDependency = Annotated[ServiceRegistry, Depends(get_registry)]


@router.get("/discover", response_model=list[ServiceDescriptor])
def discover_services(
    capability: Annotated[str, Query(min_length=1, max_length=80)],
    registry: RegistryDependency,
) -> list[ServiceDescriptor]:
    return registry.discover(capability)


@router.post(
    "/services",
    response_model=ServiceDescriptor,
    status_code=status.HTTP_201_CREATED,
)
def register_service(
    registration: ServiceRegistration,
    registry: RegistryDependency,
) -> ServiceDescriptor:
    try:
        return registry.register(registration)
    except DuplicateServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Service '{exc.args[0]}' is already registered",
        ) from exc


@router.get("/services", response_model=list[ServiceDescriptor])
def list_services(registry: RegistryDependency) -> list[ServiceDescriptor]:
    return registry.list_services()


@router.get("/services/{service_name}", response_model=ServiceDescriptor)
def get_service(
    service_name: Annotated[
        str,
        Path(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=80),
    ],
    registry: RegistryDependency,
) -> ServiceDescriptor:
    service = registry.get_service(service_name)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_name}' was not found",
        )
    return service
