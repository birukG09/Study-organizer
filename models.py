from app import db
from datetime import datetime
from enum import Enum

class DocumentStatus(Enum):
    TO_READ = "to_read"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False, unique=True)
    original_filename = db.Column(db.String(255))
    file_type = db.Column(db.String(10), nullable=False)  # 'pdf', 'epub'
    file_size = db.Column(db.Integer)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum(DocumentStatus), default=DocumentStatus.TO_READ)
    source_url = db.Column(db.Text)  # For web-to-PDF conversions
    description = db.Column(db.Text)
    view_count = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Document {self.title}>'
    
    def get_status_display(self):
        status_map = {
            DocumentStatus.TO_READ: "📘 To Read",
            DocumentStatus.IN_PROGRESS: "📖 In Progress",
            DocumentStatus.COMPLETED: "✅ Completed"
        }
        return status_map.get(self.status, "Unknown")
    
    def get_status_class(self):
        status_class = {
            DocumentStatus.TO_READ: "text-info",
            DocumentStatus.IN_PROGRESS: "text-warning",
            DocumentStatus.COMPLETED: "text-success"
        }
        return status_class.get(self.status, "text-secondary")
