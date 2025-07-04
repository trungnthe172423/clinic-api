from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import List
import sqlite3
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from .database import init_db, get_db
from .auth import create_access_token, get_current_user, User

app = FastAPI()

# Initialize database
init_db()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic models
class Patient(BaseModel):
    name: str
    date_of_birth: str
    phone: str
    address: str

class Doctor(BaseModel):
    name: str
    specialty: str

class Staff(BaseModel):
    name: str

class Appointment(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_time: str
    status: str

class Prescription(BaseModel):
    patient_id: int
    doctor_id: int
    medications: str
    date_issued: str

class PatientCreate(Patient):
    password: str

# API Endpoints
@app.post("/patients", response_model=dict)
async def create_patient(patient: PatientCreate, db: sqlite3.Connection = Depends(get_db)):
    hashed_password = pwd_context.hash(patient.password)
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO patients (name, date_of_birth, phone, address, password) VALUES (?, ?, ?, ?, ?)",
        (patient.name, patient.date_of_birth, patient.phone, patient.address, hashed_password)
    )
    patient_id = cursor.lastrowid
    db.commit()
    token = create_access_token({"sub": str(patient_id), "role": "patient"})
    return {"id": patient_id, "access_token": token, "token_type": "bearer"}

@app.get("/patients", response_model=List[Patient])
async def get_patients(current_user: User = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    if current_user.role != "staff":
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor()
    cursor.execute("SELECT name, date_of_birth, phone, address FROM patients")
    patients = [{"name": row[0], "date_of_birth": row[1], "phone": row[2], "address": row[3]} for row in cursor.fetchall()]
    return patients

@app.get("/patients/{id}", response_model=Patient)
async def get_patient(id: int, db: sqlite3.Connection = Depends(get_db)):
    # BOLA: No authorization check
    cursor = db.cursor()
    cursor.execute("SELECT name, date_of_birth, phone, address FROM patients WHERE id = ?", (id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"name": row[0], "date_of_birth": row[1], "phone": row[2], "address": row[3]}

@app.put("/patients/{id}", response_model=Patient)
async def update_patient(id: int, patient: Patient, db: sqlite3.Connection = Depends(get_db)):
    # BOLA: No authorization check
    cursor = db.cursor()
    cursor.execute(
        "UPDATE patients SET name = ?, date_of_birth = ?, phone = ?, address = ? WHERE id = ?",
        (patient.name, patient.date_of_birth, patient.phone, patient.address, id)
    )
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@app.delete("/patients/{id}")
async def delete_patient(id: int, db: sqlite3.Connection = Depends(get_db)):
    # BOLA: No authorization check
    cursor = db.cursor()
    cursor.execute("DELETE FROM patients WHERE id = ?", (id,))
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"detail": "Patient deleted"}

@app.post("/doctors", response_model=dict)
async def create_doctor(doctor: Doctor, current_user: User = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    if current_user.role != "staff":
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor()
    cursor.execute("INSERT INTO doctors (name, specialty) VALUES (?, ?)", (doctor.name, doctor.specialty))
    doctor_id = cursor.lastrowid
    db.commit()
    return {"id": doctor_id}

@app.get("/doctors", response_model=List[Doctor])
async def get_doctors(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT name, specialty FROM doctors")
    doctors = [{"name": row[0], "specialty": row[1]} for row in cursor.fetchall()]
    return doctors

@app.get("/doctors/{id}", response_model=Doctor)
async def get_doctor(id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT name, specialty FROM doctors WHERE id = ?", (id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return {"name": row[0], "specialty": row[1]}

@app.post("/staff", response_model=dict)
async def create_staff(staff: Staff, current_user: User = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    if current_user.role != "staff":
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor()
    cursor.execute("INSERT INTO staff (name) VALUES (?)", (staff.name,))
    staff_id = cursor.lastrowid
    db.commit()
    return {"id": staff_id}

@app.get("/appointments", response_model=List[Appointment])
async def get_appointments(current_user: User = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    if current_user.role == "patient":
        cursor.execute("SELECT patient_id, doctor_id, appointment_time, status FROM appointments WHERE patient_id = ?", (current_user.id,))
    elif current_user.role == "doctor":
        cursor.execute("SELECT patient_id, doctor_id, appointment_time, status FROM appointments WHERE doctor_id = ?", (current_user.id,))
    else:  # staff
        cursor.execute("SELECT patient_id, doctor_id, appointment_time, status FROM appointments")
    appointments = [{"patient_id": row[0], "doctor_id": row[1], "appointment_time": row[2], "status": row[3]} for row in cursor.fetchall()]
    return appointments

@app.get("/appointments/{id}", response_model=Appointment)
async def get_appointment(id: int, db: sqlite3.Connection = Depends(get_db)):
    # BOLA: No authorization check
    cursor = db.cursor()
    cursor.execute("SELECT patient_id, doctor_id, appointment_time, status FROM appointments WHERE id = ?", (id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"patient_id": row[0], "doctor_id": row[1], "appointment_time": row[2], "status": row[3]}

@app.post("/appointments", response_model=dict)
async def create_appointment(appointment: Appointment, current_user: User = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    if current_user.role not in ["patient", "staff"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO appointments (patient_id, doctor_id, appointment_time, status) VALUES (?, ?, ?, ?)",
        (appointment.patient_id, appointment.doctor_id, appointment.appointment_time, appointment.status)
    )
    appointment_id = cursor.lastrowid
    db.commit()
    return {"id": appointment_id}

@app.put("/appointments/{id}", response_model=Appointment)
async def update_appointment(id: int, appointment: Appointment, db: sqlite3.Connection = Depends(get_db)):
    # BOLA: No authorization check
    cursor = db.cursor()
    cursor.execute(
        "UPDATE appointments SET patient_id = ?, doctor_id = ?, appointment_time = ?, status = ? WHERE id = ?",
        (appointment.patient_id, appointment.doctor_id, appointment.appointment_time, appointment.status, id)
    )
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

@app.delete("/appointments/{id}")
async def delete_appointment(id: int, db: sqlite3.Connection = Depends(get_db)):
    # BOLA: No authorization check
    cursor = db.cursor()
    cursor.execute("DELETE FROM appointments WHERE id = ?", (id,))
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"detail": "Appointment deleted"}

@app.post("/prescriptions", response_model=dict)
async def create_prescription(prescription: Prescription, current_user: User = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO prescriptions (patient_id, doctor_id, medications, date_issued) VALUES (?, ?, ?, ?)",
        (prescription.patient_id, prescription.doctor_id, prescription.medications, prescription.date_issued)
    )
    prescription_id = cursor.lastrowid
    db.commit()
    return {"id": prescription_id}