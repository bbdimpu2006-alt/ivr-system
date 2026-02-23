from .celery_app import celery_app

@celery_app.task
def process_call_recording(recording_path: str):
    """Process call recording asynchronously"""
    # TODO: Add recording processing logic
    return {'status': 'processed', 'path': recording_path}

@celery_app.task
def send_notification(user_id: int, message: str):
    """Send notification to user"""
    # TODO: Add notification logic
    return {'status': 'sent', 'user_id': user_id}
