from flask import Flask
from app.routes import bp
from app.models import db
import os

def create_app():
    app = Flask(__name__,
                template_folder='app/templates',
                static_folder='app/static')
    
    # 템플릿 자동 리로드 설정 추가
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    # 데이터베이스 설정
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///youtube.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.urandom(24)
    
    # 데이터베이스 초기화
    db.init_app(app)
    
    # 블루프린트 등록
    app.register_blueprint(bp)
    
    # 데이터베이스 생성
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.jinja_env.auto_reload = True
    app.run(host='127.0.0.1', port=5001, debug=True) 