"""
Extended models for revision system and advanced functionality
"""

from main import db
from datetime import datetime
from sqlalchemy import Text

class CampaignRevision(db.Model):
    """Track user revision requests and feedback"""
    __tablename__ = 'campaign_revisions'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    revision_type = db.Column(db.String(50), nullable=False)  # 'text', 'image', 'video'
    user_notes = db.Column(Text, nullable=False)
    original_content = db.Column(Text)
    revised_content = db.Column(Text)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'completed', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationship
    campaign = db.relationship('Campaign', backref='revisions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'revision_type': self.revision_type,
            'user_notes': self.user_notes,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class QualityAssessment(db.Model):
    """Store quality assessment results"""
    __tablename__ = 'quality_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    assessment_type = db.Column(db.String(50), nullable=False)  # 'text', 'image', 'video'
    overall_score = db.Column(db.Float)
    passes_check = db.Column(db.Boolean, default=False)
    issues_found = db.Column(Text)  # JSON string
    recommendations = db.Column(Text)  # JSON string
    assessment_data = db.Column(Text)  # Full assessment JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    campaign = db.relationship('Campaign', backref='quality_assessments')


class ExportLog(db.Model):
    """Track data exports"""
    __tablename__ = 'export_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'))
    export_type = db.Column(db.String(50), nullable=False)  # 'campaign', 'bulk', 'analytics'
    export_format = db.Column(db.String(20), nullable=False)  # 'json', 'csv', 'txt'
    file_size = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='export_logs')
    campaign = db.relationship('Campaign', backref='export_logs')