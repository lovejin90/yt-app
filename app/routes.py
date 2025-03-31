from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from .youtube_service import get_recent_videos_by_topic, get_trending_keywords, get_trending_videos
from .models import db, APIKey, RecentSearch
from datetime import datetime
import requests
import uuid
from sqlalchemy import text

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return render_template('index.html', title='홈')

@bp.route('/settings')
def settings():
    api_keys = APIKey.query.order_by(APIKey.created_at.desc()).all()
    return render_template('settings.html', api_keys=api_keys)

@bp.route('/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': '검색어를 입력해주세요'})

    try:
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        session_id = session['session_id']

        # 테이블 구조 확인을 위한 디버그 코드
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='recent_search'"))
            table_info = result.fetchone()
            print("Table structure:", table_info[0] if table_info else "Table not found")

        # 기존 동일 검색어 삭제
        RecentSearch.query.filter_by(keyword=query, session_id=session_id).delete()
        
        # 현재 세션의 최근 검색어 개수가 15개를 초과하면 가장 오래된 검색어 삭제
        count = RecentSearch.query.filter_by(session_id=session_id).count()
        if count >= 15:
            oldest_searches = RecentSearch.query.filter_by(session_id=session_id).order_by(RecentSearch.searched_at.asc()).limit(count - 14).all()
            for search in oldest_searches:
                db.session.delete(search)
        
        # 새 검색어 추가
        recent_search = RecentSearch(keyword=query, session_id=session_id)
        db.session.add(recent_search)
        db.session.commit()

        videos = get_recent_videos_by_topic(query)
        if not videos:
            return jsonify({'items': []})
        return jsonify({'items': videos})
    except Exception as e:
        db.session.rollback()
        print(f"Search error: {str(e)}")
        return jsonify({
            'error': '검색 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
            'details': str(e)
        }), 500

@bp.route('/trending-videos')
def trending_videos():
    try:
        videos = get_trending_videos()
        return jsonify(videos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/trending-keywords')
def trending_keywords():
    try:
        keywords = get_trending_keywords()
        return jsonify(keywords)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/admin')
def admin():
    api_keys = APIKey.query.order_by(APIKey.created_at.desc()).all()
    return render_template('admin.html', api_keys=api_keys)

@bp.route('/admin/add_key', methods=['POST'])
def add_key():
    key = request.form.get('key')
    description = request.form.get('description')
    
    if not key or not description:
        flash('API 키와 설명을 모두 입력해주세요.', 'error')
        return redirect(url_for('main.admin'))
    
    try:
        new_key = APIKey(key=key, description=description)
        db.session.add(new_key)
        db.session.commit()
        flash('API 키가 추가되었습니다.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('API 키 추가 중 오류가 발생했습니다.', 'error')
    
    return redirect(url_for('main.admin'))

@bp.route('/admin/toggle_key/<int:key_id>', methods=['POST'])
def toggle_key(key_id):
    api_key = APIKey.query.get_or_404(key_id)
    api_key.is_active = not api_key.is_active
    db.session.commit()
    return jsonify({'status': 'success', 'is_active': api_key.is_active})

@bp.route('/admin/delete_key/<int:key_id>', methods=['POST'])
def delete_key(key_id):
    api_key = APIKey.query.get_or_404(key_id)
    db.session.delete(api_key)
    db.session.commit()
    flash('API 키가 삭제되었습니다.', 'success')
    return redirect(url_for('main.admin'))

@bp.route('/api/check-key')
def check_api_key():
    active_key = APIKey.query.filter_by(is_active=True).first()
    return jsonify({'hasActiveKey': active_key is not None})

@bp.route('/recent-searches')
def get_recent_searches():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    session_id = session['session_id']
    
    recent_searches = RecentSearch.query.filter_by(session_id=session_id).order_by(RecentSearch.searched_at.desc()).limit(15).all()
    return jsonify([{
        'id': search.id,
        'keyword': search.keyword,
        'searched_at': search.searched_at.strftime('%Y-%m-%d %H:%M:%S')
    } for search in recent_searches])

@bp.route('/recent-searches/delete/<int:search_id>', methods=['DELETE'])
def delete_recent_search(search_id):
    search = RecentSearch.query.get_or_404(search_id)
    db.session.delete(search)
    db.session.commit()
    return jsonify({'message': '삭제되었습니다'}) 