from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import csv
import os
import time

app = FastAPI(title="Employee API")

# ----------------------------
# CORS CONFIGURATION
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # Or use ["http://localhost:8080"]
    allow_credentials=True,
    allow_methods=["*"],            # Enables OPTIONS for preflight
    allow_headers=["*"],
)

# ----------------------------
# DATA MODELS
# ----------------------------
class Employee(BaseModel):
    id: int
    name: str
    role: str
    salary: float

class EmployeeInput(BaseModel):
    name: str
    role: str
    salary: float

# ----------------------------
# CSV FILE PATH
# ----------------------------
CSV_FILE = "employees.csv"
employees: List[Employee] = []

# ----------------------------
# CSV FUNCTIONS
# ----------------------------
def load_employees_from_csv():
    """Load all employees from CSV at startup."""
    global employees
    employees = []

    if not os.path.exists(CSV_FILE):
        # Create empty CSV with header
        with open(CSV_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["id", "name", "role", "salary"])
        return

    with open(CSV_FILE, mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            employees.append(
                Employee(
                    id=int(row["id"]),
                    name=row["name"],
                    role=row["role"],
                    salary=float(row["salary"]),
                )
            )


def save_employee_to_csv(emp: Employee):
    """Append a new employee to CSV."""
    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["id", "name", "role", "salary"])
        writer.writerow([emp.id, emp.name, emp.role, emp.salary])


# Load CSV when API starts
load_employees_from_csv()

# ----------------------------
# REQUEST PER SECOND TRACKING
# ----------------------------
WINDOW_SECONDS = 1.0
request_times: List[float] = []

@app.middleware("http")
async def count_requests(request: Request, call_next):
    now = time.time()
    request_times.append(now)

    # remove timestamps older than 1 second
    cutoff = now - WINDOW_SECONDS
    while request_times and request_times[0] < cutoff:
        request_times.pop(0)

    response = await call_next(request)
    return response


# ----------------------------
# API ENDPOINTS
# ----------------------------

# 1) Health Check
@app.get("/health")
def health_check():
    return {"status": "ok"}


# 2) Add employee (AUTO-GENERATED ID)
@app.post("/employees", response_model=Employee)
def add_employee(emp: EmployeeInput):
    # Auto ID generation
    new_id = 1 if not employees else max(e.id for e in employees) + 1

    new_emp = Employee(
        id=new_id,
        name=emp.name,
        role=emp.role,
        salary=emp.salary,
    )

    employees.append(new_emp)
    save_employee_to_csv(new_emp)
    return new_emp


# 3) Get all employees
@app.get("/employees", response_model=List[Employee])
def get_employees():
    return employees


# 4) Requests Per Second
@app.get("/metrics/rps")
def get_rps():
    now = time.time()
    cutoff = now - WINDOW_SECONDS
    recent = [t for t in request_times if t >= cutoff]
    rps = len(recent) / WINDOW_SECONDS

    return {
        "requests_per_second": round(rps, 3),
        "window_seconds": WINDOW_SECONDS,
        "total_buffered_requests": len(request_times),
    }
