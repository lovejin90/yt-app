# 유튜브 인기검색어

실시간으로 유튜브의 인기 있는 동영상과 키워드를 분석하여 보여주는 웹 애플리케이션입니다.

## 주요 기능

- 실시간 인기 키워드 순위 표시
- 인기 동영상 목록 제공
- 키워드 검색 기능
- 최근 검색어 기록
- 도메인 및 불용어 필터링

## 기술 스택

- Backend: Python 3.9, Flask
- Frontend: HTML5, CSS3, JavaScript
- Database: SQLite
- API: YouTube Data API v3

## 설치 방법

1. 저장소 클론
```bash
git clone [repository-url]
cd [repository-name]
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정
- `.env` 파일을 생성하고 다음 내용을 추가:
```
YOUTUBE_API_KEY=your_api_key_here
```

5. 데이터베이스 초기화
```bash
flask db upgrade
```

6. 서버 실행
```bash
python app.py
```

## YouTube API 키 발급 방법

1. [Google Cloud Console](https://console.cloud.google.com)에 접속
2. 새 프로젝트 생성
3. YouTube Data API v3 활성화
4. API 키 생성
5. 생성된 키를 `.env` 파일에 추가

## 프로젝트 구조

```
.
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── models.py
│   ├── youtube_service.py
│   └── templates/
│       ├── base.html
│       └── index.html
├── migrations/
├── .env
├── .gitignore
├── app.py
├── config.py
└── requirements.txt
```

## 주요 기능 설명

### 인기 키워드 분석
- YouTube API를 통해 인기 동영상의 제목과 설명을 분석
- 불용어 및 도메인 필터링을 통한 의미 있는 키워드 추출
- 조회수 기반 가중치 적용

### 실시간 업데이트
- 주기적으로 데이터 갱신
- 최신 트렌드 반영
- 실시간 검색어 순위 제공

### 사용자 인터페이스
- 반응형 디자인
- 직관적인 UI/UX
- 다크 모드 지원

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 기여 방법

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 문의사항

프로젝트에 대한 문의사항이 있으시면 Issues를 통해 남겨주세요.
