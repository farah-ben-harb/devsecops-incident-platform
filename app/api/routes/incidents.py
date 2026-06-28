from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.incident import IncidentCreate, IncidentResponse, IncidentUpdate
from app.services import incident_service
from app.telemetry.metrics import INCIDENT_CREATED_TOTAL

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentResponse])
def list_incidents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[IncidentResponse]:
    return incident_service.list_incidents(db=db, skip=skip, limit=limit)


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
) -> IncidentResponse:
    incident = incident_service.create_incident(db=db, payload=payload)
    INCIDENT_CREATED_TOTAL.labels(
        service_name=incident.service_name,
        severity=incident.severity.value,
    ).inc()
    return incident


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: int, db: Session = Depends(get_db)) -> IncidentResponse:
    incident = incident_service.get_incident(db=db, incident_id=incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.put("/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: int,
    payload: IncidentUpdate,
    db: Session = Depends(get_db),
) -> IncidentResponse:
    incident = incident_service.get_incident(db=db, incident_id=incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident_service.update_incident(db=db, incident=incident, payload=payload)


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_incident(incident_id: int, db: Session = Depends(get_db)) -> Response:
    incident = incident_service.get_incident(db=db, incident_id=incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    incident_service.delete_incident(db=db, incident=incident)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

