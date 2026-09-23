import time
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Traffic-Sim Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


# --- Request/response shapes ---
# Pydantic models like this do two things: validate incoming data
# (reject bad requests automatically) and show up in /docs so the
# API is self-documenting.

class Bounds(BaseModel):
    north: float
    south: float
    east: float
    west: float


class SimulateRequest(BaseModel):
    bounds: Bounds


# In-memory "database" for now — a plain dict. Fine for development;
# this disappears every time the server restarts. Real persistence
# (PostgreSQL, per your doc) comes later.
jobs = {}


@app.post("/simulate")
def start_simulation(request: SimulateRequest):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "running",
        "stageIndex": 0,
        "startedAt": time.time(),
        "bounds": request.bounds.dict(),
    }
    return {"jobId": job_id}


@app.get("/status/{job_id}")
def get_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Fake progress: advance one stage every 2 seconds since start,
    # so your frontend's JobStatus polling has something real to show
    # instead of jumping straight to "complete."
    elapsed = time.time() - job["startedAt"]
    stage_index = min(int(elapsed // 2), 4)
    job["stageIndex"] = stage_index

    if stage_index >= 4:
        job["status"] = "complete"

    response = {"status": job["status"], "stageIndex": stage_index}

    if job["status"] == "complete":
        response["trips"] = [
            {
                "path": [[72.877, 19.076], [72.879, 19.078], [72.881, 19.080]],
                "timestamps": [0, 10, 20],
                "vehicleType": "car",
            },
            {
                "path": [[72.876, 19.075], [72.878, 19.077], [72.880, 19.079]],
                "timestamps": [0, 5, 15],
                "vehicleType": "twoWheeler",
            },
        ]
        response["speedOverTime"] = [
            {"time": 0, "avgSpeed": 24},
            {"time": 10, "avgSpeed": 21},
            {"time": 20, "avgSpeed": 19},
        ]
        response["vehicleMix"] = [
            {"type": "car", "count": 120},
            {"type": "twoWheeler", "count": 340},
        ]
        response["validation"] = {"mape": 8.4, "geh": 3.1}

    return response