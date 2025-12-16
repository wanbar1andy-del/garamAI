# GARAM Slack Alert 설정 가이드

## Slack Webhook URL 생성

### 1. Slack Workspace 접속

- <https://api.slack.com/apps>

### 2. Create New App

1. "Create New App" 클릭
2. "From scratch" 선택
3. App Name: "GARAM Alerts"
4. Workspace 선택

### 3. Incoming Webhooks 활성화

1. 좌측 메뉴에서 "Incoming Webhooks" 클릭
2. "Activate Incoming Webhooks" ON
3. "Add New Webhook to Workspace" 클릭
4. 알림 받을 채널 선택 (예: #garam-alerts)
5. "Allow" 클릭

### 4. Webhook URL 복사

```
https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

## 환경 변수 설정

### Windows 환경 변수 등록

#### 방법 1: 시스템 설정 (권장)

1. Win + R → `sysdm.cpl` 실행
2. "고급" 탭 → "환경 변수" 클릭
3. "사용자 변수" 섹션에서 "새로 만들기"
4. 변수 이름: `GARAM_SLACK_WEBHOOK`
5. 변수 값: 복사한 Webhook URL 붙여넣기
6. 확인 → 재시작

#### 방법 2: PowerShell (임시)

```powershell
$env:GARAM_SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

#### 방법 3: .env 파일

```
# c:\garam\garam\.env
GARAM_SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## 테스트

### Python에서 직접 테스트

```python
import os
import requests

webhook = os.environ.get('GARAM_SLACK_WEBHOOK')
if webhook:
    requests.post(webhook, json={'text': '🚀 GARAM Test Alert'})
    print("Alert sent!")
else:
    print("Webhook not configured")
```

### 테스트 스크립트 실행

```powershell
python -c "import os, requests; requests.post(os.environ['GARAM_SLACK_WEBHOOK'], json={'text': '✅ GARAM 알림 테스트'})"
```

## 알림 레벨별 사용

### Info (정보)

```python
send_alert("시스템 시작 완료", 'info')  # ✅
```

### Warning (경고)

```python
send_alert("Dashboard 재시작 중", 'warning')  # ⚠️
```

### Critical (긴급)

```python
send_alert("수동 개입 필요", 'critical')  # 🚨
```

## 문제 해결

### Webhook URL이 없을 때

- 알림이 전송되지 않지만 시스템은 정상 작동
- 로그 파일에만 기록됨

### 전송 실패 시

- 네트워크 연결 확인
- Webhook URL 유효성 확인
- Slack App 활성화 상태 확인

## 다음 단계 (선택)

### SMS 알림 추가

- Twilio, AWS SNS 등 사용
- Critical 레벨에만 SMS 전송

### 이메일 알림 추가

- SMTP 설정
- Gmail, Outlook 등 사용

---

**Status**: 📝 설정 가이드  
**Priority**: P0  
**Required**: Webhook URL만 설정하면 즉시 사용 가능
