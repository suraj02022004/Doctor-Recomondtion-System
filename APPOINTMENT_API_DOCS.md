# Appointment Management API Documentation

## Overview
Complete REST API for managing doctor appointments with features for creation, retrieval, status tracking, and analytics.

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
All endpoints support optional JWT authentication. Include token in Authorization header:
```
Authorization: Bearer <your-token>
```

## Endpoints

### 1. Create Appointment
**POST** `/appointments/`

Request body:
```json
{
  "patient_email": "john@example.com",
  "patient_name": "John Doe",
  "doctor_name": "Dr. Smith",
  "doctor_id": "1",
  "appointment_date": "2026-05-15",
  "appointment_time": "10:00",
  "reason": "General Checkup"
}
```

Response:
```json
{
  "id": "1",
  "patient_email": "john@example.com",
  "patient_name": "John Doe",
  "doctor_name": "Dr. Smith",
  "doctor_id": "1",
  "appointment_date": "2026-05-15",
  "appointment_time": "10:00",
  "reason": "General Checkup",
  "status": "pending",
  "notes": "",
  "created_at": "2026-04-30T10:00:00"
}
```

### 2. List All Appointments
**GET** `/appointments/`

Query Parameters:
- `skip` (int, default: 0) - Number of records to skip
- `limit` (int, default: 10, max: 100) - Number of records to return
- `patient_email` (string, optional) - Filter by patient email
- `doctor_id` (string, optional) - Filter by doctor ID
- `status` (string, optional) - Filter by status (pending, confirmed, completed, cancelled, no-show)

Example: `/appointments/?status=confirmed&limit=20`

### 3. Get Specific Appointment
**GET** `/appointments/{appointment_id}`

Response: Single appointment object

### 4. Get Patient Appointments
**GET** `/appointments/patient/{patient_email}`

Returns all appointments for a specific patient.

### 5. Get Doctor Appointments
**GET** `/appointments/doctor/{doctor_id}`

Returns all appointments for a specific doctor.

### 6. Get Seen (Completed) Appointments
**GET** `/appointments/seen/completed`

Query Parameters:
- `patient_email` (string, optional)
- `skip` (int, default: 0)
- `limit` (int, default: 10)

Returns completed appointments in reverse chronological order.

### 7. Get Upcoming Appointments
**GET** `/appointments/upcoming/list`

Query Parameters:
- `patient_email` (string, optional)
- `skip` (int, default: 0)
- `limit` (int, default: 10)

Returns future appointments sorted by date and time.

### 8. Update Appointment Status
**PUT** `/appointments/{appointment_id}/status`

Request body:
```json
{
  "status": "confirmed"
}
```

Valid status values:
- `pending`
- `confirmed`
- `completed`
- `cancelled`
- `no-show`

### 9. Update Appointment Notes
**PUT** `/appointments/{appointment_id}/notes`

Request body:
```json
{
  "notes": "Patient requires special attention"
}
```

### 10. Confirm Appointment
**POST** `/appointments/{appointment_id}/confirm`

Changes status to "confirmed"

### 11. Mark as Completed
**POST** `/appointments/{appointment_id}/complete`

Changes status to "completed"

### 12. Mark as No-Show
**POST** `/appointments/{appointment_id}/no-show`

Changes status to "no-show"

### 13. Cancel Appointment
**POST** `/appointments/{appointment_id}/cancel`

Changes status to "cancelled"

### 14. Delete Appointment
**DELETE** `/appointments/{appointment_id}`

Response:
```json
{
  "message": "Appointment 1 deleted successfully"
}
```

### 15. Get Doctor Statistics
**GET** `/appointments/stats/doctor/{doctor_id}`

Response:
```json
{
  "total_appointments": 45,
  "pending": 10,
  "confirmed": 20,
  "completed": 10,
  "cancelled": 3,
  "no_show": 2
}
```

### 16. Get Overall Statistics
**GET** `/appointments/stats/all`

Response: System-wide appointment statistics

### 17. Get Paginated Appointments
**GET** `/appointments/paginated/list`

Query Parameters:
- `page` (int, default: 1, min: 1)
- `page_size` (int, default: 10, min: 1, max: 100)
- `patient_email` (string, optional)
- `doctor_id` (string, optional)
- `status` (string, optional)

Response:
```json
{
  "total": 100,
  "page": 1,
  "page_size": 10,
  "total_pages": 10,
  "appointments": [...]
}
```

## Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `500` - Internal Server Error

## Error Response

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Appointment Status Workflow

```
pending → confirmed → completed
  ↓                      ↓
  └─────→ cancelled     no-show
```

## Features

✅ Create, read, update, delete appointments
✅ Filter by patient, doctor, date, status
✅ Sort appointments (chronological, reverse chronological, by doctor, by patient, by status)
✅ Pagination support
✅ Status tracking and management
✅ Statistics and analytics
✅ Data persistence (JSON/Database)
✅ CSV export capability
✅ JWT authentication
✅ CORS support
✅ Interactive API documentation at `/docs`

## Running Tests

```bash
pytest tests/test_appointments.py -v
```

## Example Usage with cURL

Create appointment:
```bash
curl -X POST "http://localhost:8000/api/v1/appointments/" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_email": "john@example.com",
    "patient_name": "John Doe",
    "doctor_name": "Dr. Smith",
    "doctor_id": "1",
    "appointment_date": "2026-05-15",
    "appointment_time": "10:00",
    "reason": "General Checkup"
  }'
```

Get seen appointments:
```bash
curl -X GET "http://localhost:8000/api/v1/appointments/seen/completed?limit=5"
```

Get statistics:
```bash
curl -X GET "http://localhost:8000/api/v1/appointments/stats/all"
```

## Support

For issues or questions, please open an issue in the repository.