"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
import secrets
from datetime import datetime
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database helpers

def create_activity(description, schedule, max_participants, participants):
    return {
        "description": description,
        "schedule": schedule,
        "max_participants": max_participants,
        "participants": participants,
        "qr_token": secrets.token_urlsafe(12),
        "attendance": []
    }


def get_last_attendance(activity, email):
    for record in reversed(activity["attendance"]):
        if record["email"] == email:
            return record
    return None


def record_attendance(activity, email, action):
    attendance_entry = {
        "email": email,
        "action": action,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    activity["attendance"].append(attendance_entry)
    return attendance_entry


def validate_qr_token(activity, token):
    if token != activity["qr_token"]:
        raise HTTPException(status_code=400, detail="Invalid QR token")


# In-memory activity database
activities = {
    "Chess Club": create_activity(
        "Learn strategies and compete in chess tournaments",
        "Fridays, 3:30 PM - 5:00 PM",
        12,
        ["michael@mergington.edu", "daniel@mergington.edu"]
    ),
    "Programming Class": create_activity(
        "Learn programming fundamentals and build software projects",
        "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        20,
        ["emma@mergington.edu", "sophia@mergington.edu"]
    ),
    "Gym Class": create_activity(
        "Physical education and sports activities",
        "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        30,
        ["john@mergington.edu", "olivia@mergington.edu"]
    ),
    "Soccer Team": create_activity(
        "Join the school soccer team and compete in matches",
        "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        22,
        ["liam@mergington.edu", "noah@mergington.edu"]
    ),
    "Basketball Team": create_activity(
        "Practice and play basketball with the school team",
        "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        15,
        ["ava@mergington.edu", "mia@mergington.edu"]
    ),
    "Art Club": create_activity(
        "Explore your creativity through painting and drawing",
        "Thursdays, 3:30 PM - 5:00 PM",
        15,
        ["amelia@mergington.edu", "harper@mergington.edu"]
    ),
    "Drama Club": create_activity(
        "Act, direct, and produce plays and performances",
        "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        20,
        ["ella@mergington.edu", "scarlett@mergington.edu"]
    ),
    "Math Club": create_activity(
        "Solve challenging problems and participate in math competitions",
        "Tuesdays, 3:30 PM - 4:30 PM",
        10,
        ["james@mergington.edu", "benjamin@mergington.edu"]
    ),
    "Debate Team": create_activity(
        "Develop public speaking and argumentation skills",
        "Fridays, 4:00 PM - 5:30 PM",
        12,
        ["charlotte@mergington.edu", "henry@mergington.edu"]
    )
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Validate there is space available
    if len(activity["participants"]) >= activity["max_participants"]:
        raise HTTPException(
            status_code=400,
            detail="Activity is full"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}


@app.post("/activities/{activity_name}/checkin")
def check_in(activity_name: str, email: str, token: str):
    """Check a student into an activity using an activity QR token"""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]
    validate_qr_token(activity, token)

    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not registered for this activity"
        )

    last_record = get_last_attendance(activity, email)
    if last_record and last_record["action"] == "checkin":
        raise HTTPException(
            status_code=400,
            detail="Student is already checked in"
        )

    attendance_entry = record_attendance(activity, email, "checkin")
    return {
        "message": f"{email} checked in for {activity_name}",
        "attendance": attendance_entry
    }


@app.post("/activities/{activity_name}/checkout")
def check_out(activity_name: str, email: str, token: str):
    """Check a student out of an activity using an activity QR token"""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]
    validate_qr_token(activity, token)

    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not registered for this activity"
        )

    last_record = get_last_attendance(activity, email)
    if not last_record or last_record["action"] != "checkin":
        raise HTTPException(
            status_code=400,
            detail="Student must check in before checking out"
        )

    attendance_entry = record_attendance(activity, email, "checkout")
    return {
        "message": f"{email} checked out from {activity_name}",
        "attendance": attendance_entry
    }
