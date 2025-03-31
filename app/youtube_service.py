import os
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from dateutil import parser
import pandas as pd
import re
import pytz
from collections import Counter
from .models import APIKey, db
import requests

def get_active_api_key():
    api_key = APIKey.query.filter_by(is_active=True).first()
    if not api_key:
        raise Exception("활성화된 API 키가 없습니다.")
    
    # 마지막 사용 시간 업데이트
    api_key.last_used = datetime.utcnow()
    db.session.commit()
    
    return api_key.key

def get_youtube_service():
    api_key = get_active_api_key()
    return build('youtube', 'v3', developerKey=api_key)

def get_recent_videos_by_topic(query):
    api_key = get_active_api_key()
    if not api_key:
        raise Exception('활성화된 API 키가 없습니다.')

    try:
        # 검색 요청
        search_url = 'https://www.googleapis.com/youtube/v3/search'
        search_params = {
            'part': 'snippet',
            'q': query,
            'key': api_key,
            'type': 'video',
            'maxResults': 10,
            'order': 'date'
        }
        search_response = requests.get(search_url, params=search_params)
        search_response.raise_for_status()  # HTTP 에러 체크
        search_data = search_response.json()

        if 'error' in search_data:
            raise Exception(search_data['error'].get('message', '알 수 없는 오류가 발생했습니다.'))

        if not search_data.get('items'):
            return []

        # 비디오 ID 목록 추출
        video_ids = [item['id']['videoId'] for item in search_data['items']]

        # 비디오 상세 정보 요청
        videos_url = 'https://www.googleapis.com/youtube/v3/videos'
        videos_params = {
            'part': 'snippet,statistics',
            'id': ','.join(video_ids),
            'key': api_key
        }
        videos_response = requests.get(videos_url, params=videos_params)
        videos_response.raise_for_status()  # HTTP 에러 체크
        videos_data = videos_response.json()

        if 'error' in videos_data:
            raise Exception(videos_data['error'].get('message', '알 수 없는 오류가 발생했습니다.'))

        # 결과 가공
        videos = []
        for item in videos_data.get('items', []):
            video = {
                'id': item['id'],
                'title': item['snippet']['title'],
                'thumbnail': item['snippet']['thumbnails']['medium']['url'],
                'channelTitle': item['snippet']['channelTitle'],
                'publishedAt': item['snippet']['publishedAt'],
                'viewCount': item['statistics'].get('viewCount', '0')
            }
            videos.append(video)

        return videos

    except requests.exceptions.RequestException as e:
        raise Exception(f'YouTube API 요청 중 오류가 발생했습니다: {str(e)}')
    except KeyError as e:
        raise Exception(f'응답 데이터 처리 중 오류가 발생했습니다: {str(e)}')
    except Exception as e:
        raise Exception(f'검색 중 오류가 발생했습니다: {str(e)}')

def clean_text(text):
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    # 특수문자를 공백으로 변경 (단, 한글, 영문, 숫자, 일부 특수문자 유지)
    text = re.sub(r'[^\w\s가-힣\-_]', ' ', text)
    # 여러 개의 공백을 하나로
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def is_valid_keyword(keyword):
    # 숫자로만 이루어진 키워드 제외
    if keyword.isdigit():
        return False
    # 길이가 1인 키워드 제외
    if len(keyword) < 2:
        return False
    # 도메인 패턴 필터링 (.com, .net, .org 등)
    if '.' in keyword and any(keyword.lower().endswith(tld) for tld in ['.com', '.net', '.org', '.co.kr', '.kr', '.io']):
        return False
    # 도메인 관련 키워드 필터링
    domain_related = {'https', 'http', 'www', 'com', 'kr', 'net', 'org', 'instagram', 'facebook', 'twitter', 'EC', 'EB'}
    if keyword.lower() in {x.lower() for x in domain_related}:
        return False
    # 불용어 필터링
    stopwords = {
        '있는', '없는', '그런', '이런', '저런', '다시', '이제', '우리', '서로', 
        '매일', '정말', '진짜', '계속', '하는', '이거', '저거', '그거', '때문',
        'the', 'and', 'for', 'that', 'this', 'with', 'you', 'are', 'have'
    }
    if keyword.lower() in stopwords:
        return False
    return True

def is_within_period(published_at, days=3):  # 3일로 설정
    kr_tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(kr_tz)
    video_date = parser.parse(published_at).astimezone(kr_tz)
    time_diff = now - video_date
    return time_diff.total_seconds() <= days * 24 * 60 * 60

def get_trending_keywords():
    youtube = get_youtube_service()
    
    keywords = []
    next_page_token = None
    total_results = 0
    max_results = 200  # 더 많은 영상 수집

    while total_results < max_results:
        try:
            # 인기 동영상 가져오기
            request = youtube.videos().list(
                part='snippet,statistics',
                chart='mostPopular',
                regionCode='KR',
                maxResults=50,
                pageToken=next_page_token
            )
            videos_response = request.execute()
            
            # 제목에서 키워드 추출
            for item in videos_response['items']:
                if is_within_period(item['snippet']['publishedAt']):
                    title = item['snippet']['title']
                    description = item['snippet']['description']
                    
                    # 제목과 설명 모두에서 키워드 추출
                    clean_title = clean_text(title + ' ' + description)
                    words = clean_title.split()
                    
                    # 유효한 키워드만 추가
                    valid_words = [word for word in words if is_valid_keyword(word)]
                    
                    # 조회수에 따른 가중치 부여
                    view_count = int(item['statistics'].get('viewCount', 0))
                    weight = 1
                    if view_count > 1000000:  # 100만 이상 조회수
                        weight = 3
                    elif view_count > 500000:  # 50만 이상 조회수
                        weight = 2
                        
                    keywords.extend(valid_words * weight)
            
            total_results += len(videos_response['items'])
            next_page_token = videos_response.get('nextPageToken')
            
            if not next_page_token:
                break
                
        except Exception as e:
            print(f"Error fetching videos: {e}")
            break
    
    # 키워드 빈도수 계산
    keyword_freq = pd.Series(keywords).value_counts()
    
    # 상위 15개 키워드 반환
    return [{'keyword': k, 'count': int(v)} for k, v in keyword_freq.head(15).items()]

def get_trending_videos(max_results=10):  # 10개로 증가
    youtube = get_youtube_service()
    
    try:
        # 인기 동영상 가져오기
        videos_response = youtube.videos().list(
            part='snippet,statistics',
            chart='mostPopular',
            regionCode='KR',
            maxResults=50
        ).execute()
        
        # 결과 처리
        videos = []
        for item in videos_response['items']:
            if is_within_period(item['snippet']['publishedAt']):
                try:
                    video_data = {
                        'title': item['snippet']['title'],
                        'upload_date': parser.parse(item['snippet']['publishedAt']).astimezone(pytz.timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M'),
                        'views': int(item['statistics'].get('viewCount', 0)),
                        'channel_name': item['snippet']['channelTitle'],
                        'video_id': item['id'],
                        'link': f'https://www.youtube.com/watch?v={item["id"]}',
                        'likes': int(item['statistics'].get('likeCount', 0)),
                        'comments': int(item['statistics'].get('commentCount', 0)),
                        'thumbnail': item['snippet']['thumbnails']['medium']['url']
                    }
                    videos.append(video_data)
                except Exception as e:
                    print(f"Error processing video {item.get('id', 'unknown')}: {e}")
                    continue
        
        # 조회수 기준으로 정렬
        videos.sort(key=lambda x: x['views'], reverse=True)
        return videos[:max_results]
        
    except Exception as e:
        print(f"Error fetching trending videos: {e}")
        return [] 