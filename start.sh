#!/bin/bash

# SSH 서버 시작
/usr/sbin/sshd

# Flask 앱 시작
gunicorn --bind 0.0.0.0:5000 "app:create_app()" 