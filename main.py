from fastapi import FastAPI
from routes import auth, prescription, reminder
from scheduler import start_scheduler
start_scheduler()


app = FastAPI()

app.include_router(auth.router)
app.include_router(prescription.router)
app.include_router(reminder.router)

@app.get("/")
def home():
    return {"message": "Medical App Backend Running"}
