from datetime import datetime
from . import db

class APIKey(db.Model):
    __tablename__ = 'api_keys'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)

    def __repr__(self):
        return f'<APIKey {self.key}>'

class RecentSearch(db.Model):
    __tablename__ = 'recent_search'
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.Text, nullable=False)
    session_id = db.Column(db.Text, nullable=False)
    searched_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, keyword, session_id):
        self.keyword = keyword
        self.session_id = session_id

    def __repr__(self):
        return f'<RecentSearch {self.keyword}>' 