FROM python:3.9-slim

WORKDIR /app

# 시스템 의존성 및 SSH 서버 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    openssh-server \
    && rm -rf /var/lib/apt/lists/*

# SSH 설정
RUN mkdir /var/run/sshd
RUN echo 'root:yourpassword' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH 포트 설정
EXPOSE 22

# 파이썬 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . .

# instance 디렉토리 생성
RUN mkdir -p instance

# 앱 포트 설정
EXPOSE 5000

# 환경 변수 설정
ENV FLASK_APP=app
ENV FLASK_ENV=production

# 시작 스크립트 생성
COPY start.sh /start.sh
RUN chmod +x /start.sh

# 실행 명령
CMD ["/start.sh"] 