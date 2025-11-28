from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import datetime

app = FastAPI(
    title="API de Gestión Médica",
    description="API para la gestión de pacientes, citas y expedientes médicos.",
    version="1.4.0"
)



class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserDisplay(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr
    role: str 

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int   
    role: str       
    full_name: str

class Patient(BaseModel):
    patient_id: int
    user_id: int
    name: str
    birth_date: datetime.date
    contact_info: Optional[str] = None

class PatientCreate(BaseModel):
    name: str
    birth_date: datetime.date
    contact_info: Optional[str] = None
    user_id: int 
class MedicalRecord(BaseModel):
    record_id: int
    patient_id: int
    record_date: datetime.datetime
    notes: str
    weight_kg: float
    blood_pressure: str
    treatment: Optional[str] = None
    photo_url: Optional[str] = None 

class MedicalRecordCreate(BaseModel):
    notes: str
    weight_kg: float
    blood_pressure: str
    treatment: Optional[str] = None
    photo_url: Optional[str] = None

class Appointment(BaseModel):
    appointment_id: int
    patient_id: int
    appointment_date: datetime.datetime
    reason: str
    doctor_name: Optional[str] = None
    status: str = "Programada"

class AppointmentCreate(BaseModel):
    patient_id: int
    appointment_date: datetime.datetime
    reason: str
    doctor_name: Optional[str] = None


fake_db = {
   
    "users": [
        {"user_id": 1, "full_name": "Admin", "email": "admin@test.com", "password_hash": "hashed_fakepassword123", "role": "admin"}
    ],
    "patients": [
        {"patient_id": 1, "user_id": 1, "name": "Juan Perez", "birth_date": datetime.date(1990, 5, 15), "contact_info": "555-1234"},
        {"patient_id": 2, "user_id": 1, "name": "Ana Garcia", "birth_date": datetime.date(1985, 11, 20), "contact_info": "555-5678"}
    ],
    "medical_records": [
        {"record_id": 1, "patient_id": 1, "record_date": datetime.datetime.now(), "notes": "Gripe estacional.", "weight_kg": 75.5, "blood_pressure": "120/80", "treatment": "Paracetamol", "photo_url": None}
    ],
    "appointments": []
}

next_user_id = 2
next_patient_id = 3
next_record_id = 2
next_appointment_id = 1


@app.post("/doctors", response_model=UserDisplay)
async def create_doctor(user: UserRegister):
    """Crea un nuevo doctor (Solo debería usarse por el admin)"""
    global next_user_id
    
    if any(u['email'] == user.email for u in fake_db['users']):
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    new_user = user.dict()
    new_user.pop("password")
    new_user["user_id"] = next_user_id
    new_user["password_hash"] = f"hashed_{user.password}"
    new_user["role"] = "doctor" 
    fake_db["users"].append(new_user)
    next_user_id += 1
    return new_user

@app.post("/login", response_model=Token)
async def login(form_data: UserLogin):
    user = next((u for u in fake_db["users"] if u["email"] == form_data.email), None)
    if not user or user["password_hash"] != f"hashed_{form_data.password}":
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    return {
        "access_token": f"fake_token_{user['email']}", 
        "token_type": "bearer",
        "user_id": user['user_id'],
        "role": user['role'],
        "full_name": user['full_name']
    }



@app.get("/patients", response_model=List[Patient])
async def get_patients(user_id: int):
    """Devuelve SOLO los pacientes asignados al usuario que los pide"""
    return [p for p in fake_db["patients"] if p["user_id"] == user_id]

@app.post("/patients", response_model=Patient)
async def create_patient(patient: PatientCreate):
    global next_patient_id
 
    new_p = {**patient.dict(), "patient_id": next_patient_id}
    fake_db["patients"].append(new_p)
    next_patient_id += 1
    return new_p

@app.put("/patients/{patient_id}", response_model=Patient)
async def update_patient(patient_id: int, patient: PatientCreate):
    idx = next((i for i, p in enumerate(fake_db["patients"]) if p["patient_id"] == patient_id), None)
    if idx is None: raise HTTPException(status_code=404, detail="No encontrado")
    
   
    original_user_id = fake_db["patients"][idx]["user_id"]
    updated = {**patient.dict(), "patient_id": patient_id, "user_id": original_user_id}
    
    fake_db["patients"][idx] = updated
    return updated

@app.delete("/patients/{patient_id}", status_code=204)
async def delete_patient(patient_id: int):
    p = next((p for p in fake_db["patients"] if p["patient_id"] == patient_id), None)
    if not p: raise HTTPException(status_code=404, detail="No encontrado")
    fake_db["patients"].remove(p)
    return {}


@app.get("/patients/{patient_id}/records", response_model=List[MedicalRecord])
async def get_records(patient_id: int):
    return [r for r in fake_db["medical_records"] if r["patient_id"] == patient_id]

@app.post("/patients/{patient_id}/records", response_model=MedicalRecord)
async def create_record(patient_id: int, record: MedicalRecordCreate):
    global next_record_id
    new_r = {**record.dict(), "record_id": next_record_id, "patient_id": patient_id, "record_date": datetime.datetime.now()}
    fake_db["medical_records"].append(new_r)
    next_record_id += 1
    return new_r

@app.put("/medical_records/{record_id}", response_model=MedicalRecord)
async def update_record(record_id: int, record: MedicalRecordCreate):
    idx = next((i for i, r in enumerate(fake_db["medical_records"]) if r["record_id"] == record_id), None)
    if idx is None: raise HTTPException(status_code=404, detail="Nota no encontrada")
    original = fake_db["medical_records"][idx]
    updated = {**original, **record.dict()}
    fake_db["medical_records"][idx] = updated
    return updated

@app.delete("/medical_records/{record_id}", status_code=204)
async def delete_record(record_id: int):
    r = next((r for r in fake_db["medical_records"] if r["record_id"] == record_id), None)
    if not r: raise HTTPException(status_code=404, detail="Nota no encontrada")
    fake_db["medical_records"].remove(r)
    return {}

@app.get("/appointments", response_model=List[Appointment])
async def get_appointments():
    return fake_db["appointments"]

@app.post("/appointments", response_model=Appointment)
async def create_appointment(appt: AppointmentCreate):
    global next_appointment_id
    new_a = {**appt.dict(), "appointment_id": next_appointment_id, "status": "Programada"}
    fake_db["appointments"].append(new_a)
    next_appointment_id += 1
    return new_a

@app.put("/appointments/{appointment_id}", response_model=Appointment)
async def update_appointment(appointment_id: int, appt: AppointmentCreate):
    idx = next((i for i, a in enumerate(fake_db["appointments"]) if a["appointment_id"] == appointment_id), None)
    if idx is None: raise HTTPException(status_code=404, detail="Cita no encontrada")
    updated = {**fake_db["appointments"][idx], **appt.dict()}
    updated["patient_id"] = appt.patient_id 
    fake_db["appointments"][idx] = updated
    return updated

@app.delete("/appointments/{appointment_id}", status_code=204)
async def delete_appointment(appointment_id: int):
    a = next((a for a in fake_db["appointments"] if a["appointment_id"] == appointment_id), None)
    if not a: raise HTTPException(status_code=404, detail="No encontrada")
    fake_db["appointments"].remove(a)
    return {}