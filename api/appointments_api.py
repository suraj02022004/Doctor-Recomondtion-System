from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.appointment_manager import AppointmentManager, AppointmentStatus

router = APIRouter(prefix="/appointments", tags=["appointments"])
manager = AppointmentManager()

class AppointmentRequest(BaseModel):
    patient_email: str
    patient_name: str
    doctor_name: str
    doctor_id: str
    appointment_date: str
    appointment_time: str
    reason: str

class AppointmentResponse(BaseModel):
    id: str
    patient_email: str
    patient_name: str
    doctor_name: str
    doctor_id: str
    appointment_date: str
    appointment_time: str
    reason: str
    status: str
    notes: str
    created_at: str

class AppointmentStatusUpdate(BaseModel):
    status: str

class AppointmentNotesUpdate(BaseModel):
    notes: str

@router.post("/", response_model=AppointmentResponse)
def create_appointment(appointment: AppointmentRequest):
    """Create a new appointment"""
    result = manager.add_appointment(
        patient_email=appointment.patient_email,
        patient_name=appointment.patient_name,
        doctor_name=appointment.doctor_name,
        doctor_id=appointment.doctor_id,
        appointment_date=appointment.appointment_date,
        appointment_time=appointment.appointment_time,
        reason=appointment.reason
    )
    return result

@router.get("/", response_model=List[AppointmentResponse])
def list_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    patient_email: Optional[str] = None,
    doctor_id: Optional[str] = None,
    status: Optional[str] = None
):
    """List all appointments with optional filtering"""
    filtered = manager.appointments
    
    if patient_email:
        filtered = [appt for appt in filtered if appt['patient_email'] == patient_email]
    if doctor_id:
        filtered = [appt for appt in filtered if appt['doctor_id'] == doctor_id]
    if status:
        filtered = [appt for appt in filtered if appt['status'] == status]
    
    return filtered[skip:skip + limit]

@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(appointment_id: str):
    """Get a specific appointment by ID"""
    appointment = manager.get_appointment_by_id(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

@router.get("/patient/{patient_email}", response_model=List[AppointmentResponse])
def get_patient_appointments(patient_email: str):
    """Get all appointments for a specific patient"""
    appointments = manager.get_appointments_by_patient(patient_email)
    if not appointments:
        raise HTTPException(status_code=404, detail="No appointments found for this patient")
    return appointments

@router.get("/doctor/{doctor_id}", response_model=List[AppointmentResponse])
def get_doctor_appointments(doctor_id: str):
    """Get all appointments for a specific doctor"""
    appointments = manager.get_appointments_by_doctor(doctor_id)
    if not appointments:
        raise HTTPException(status_code=404, detail="No appointments found for this doctor")
    return appointments

@router.get("/seen/completed", response_model=List[AppointmentResponse])
def get_seen_appointments(
    patient_email: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Get all seen (completed) appointments, arranged in reverse chronological order"""
    seen = manager.get_seen_appointments(patient_email=patient_email)
    return seen[skip:skip + limit]

@router.get("/upcoming/list", response_model=List[AppointmentResponse])
def get_upcoming_appointments(
    patient_email: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Get all upcoming appointments"""
    upcoming = manager.get_upcoming_appointments(patient_email=patient_email)
    return upcoming[skip:skip + limit]

@router.put("/{appointment_id}/status", response_model=AppointmentResponse)
def update_appointment_status(appointment_id: str, status_update: AppointmentStatusUpdate):
    """Update appointment status"""
    try:
        status_enum = AppointmentStatus(status_update.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status value")
    
    appointment = manager.update_appointment_status(appointment_id, status_enum)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

@router.put("/{appointment_id}/notes", response_model=AppointmentResponse)
def update_appointment_notes(appointment_id: str, notes_update: AppointmentNotesUpdate):
    """Update appointment notes"""
    appointment = manager.update_appointment_notes(appointment_id, notes_update.notes)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(appointment_id: str):
    """Cancel an appointment"""
    appointment = manager.cancel_appointment(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

@router.post("/{appointment_id}/complete", response_model=AppointmentResponse)
def mark_appointment_complete(appointment_id: str):
    """Mark an appointment as completed"""
    appointment = manager.mark_as_completed(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

@router.post("/{appointment_id}/confirm", response_model=AppointmentResponse)
def confirm_appointment(appointment_id: str):
    """Mark an appointment as confirmed"""
    appointment = manager.mark_as_confirmed(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

@router.post("/{appointment_id}/no-show", response_model=AppointmentResponse)
def mark_appointment_no_show(appointment_id: str):
    """Mark an appointment as no-show"""
    appointment = manager.mark_as_no_show(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

@router.delete("/{appointment_id}")
def delete_appointment(appointment_id: str):
    """Delete an appointment"""
    success = manager.delete_appointment(appointment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": f"Appointment {appointment_id} deleted successfully"}

@router.get("/stats/doctor/{doctor_id}")
def get_doctor_statistics(doctor_id: str):
    """Get appointment statistics for a doctor"""
    stats = manager.get_appointment_statistics(doctor_id=doctor_id)
    return stats

@router.get("/stats/all")
def get_all_statistics():
    """Get overall appointment statistics"""
    stats = manager.get_appointment_statistics()
    return stats

@router.get("/paginated/list", response_model=dict)
def get_appointments_paginated(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    patient_email: Optional[str] = None,
    doctor_id: Optional[str] = None,
    status: Optional[str] = None
):
    """Get paginated appointments"""
    return manager.get_appointments_paginated(
        page=page,
        page_size=page_size,
        patient_email=patient_email,
        doctor_id=doctor_id,
        status=status
    )