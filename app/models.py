# app/models.py

# Global State for Transfer Progress
transfer_status = {
    "status": "idle",  # idle, running, completed, failed
    "progress": 0,
    "log": "Chưa có hoạt động nào.",
    "thread": None
}
