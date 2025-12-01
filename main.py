from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, prescription, reminder

app = FastAPI()

# CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(prescription.router)
app.include_router(reminder.router)

@app.get("/")
def home():
    return {"message": "Medical App Backend Running"}
