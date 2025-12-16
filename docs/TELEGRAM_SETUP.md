# GARAM Telegram Bot 설정 가이드

## 1. Telegram Bot 생성

### BotFather와 대화

1. Telegram 앱 열기
2. `@BotFather` 검색 및 대화 시작
3. `/newbot` 입력
4. Bot 이름 입력 (예: `GARAM Trading Bot`)
5. Bot username 입력 (예: `garam_trading_bot`)
   - 반드시 `_bot`으로 끝나야 함

### Bot Token 저장

BotFather가 제공하는 Token 복사:

```
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

## 2. Chat ID 얻기

### 방법 1: Bot과 대화 후 확인

1. 생성한 Bot 검색 (예: `@garam_trading_bot`)
2. `/start` 명령 전송
3. 브라우저에서 아래 URL 접속:

```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```

4. 응답에서 `chat.id` 찾기:

```json
{
  "message": {
    "chat": {
      "id": 1234567890,  // <- 이것이 Chat ID
      "type": "private"
    }
  }
}
```

### 방법 2: userinfobot 사용

1. `@userinfobot` 검색
2. 대화 시작하면 자동으로 Chat ID 표시

## 3. 환경 변수 설정

### Windows 시스템 환경 변수

1. **Win + R** → `sysdm.cpl`
2. **고급** 탭 → **환경 변수**
3. **사용자 변수**에서 **새로 만들기**:

**변수 1**:

- 이름: `GARAM_TELEGRAM_BOT_TOKEN`
- 값: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

**변수 2**:

- 이름: `GARAM_TELEGRAM_CHAT_ID`
- 값: `1234567890`

4. **확인** → 컴퓨터 재시작 (또는 PowerShell 재시작)

### 확인

PowerShell에서:

```powershell
$env:GARAM_TELEGRAM_BOT_TOKEN
$env:GARAM_TELEGRAM_CHAT_ID
```

## 4. 테스트

### Python 테스트

```python
python utils/telegram_bot.py
```

예상 출력:

```
Telegram bot enabled (Chat ID: 1234567890)
Testing Telegram bot...
✅ Test messages sent!
```

### Telegram 앱 확인

Bot으로부터 메시지 수신 확인:

```
✅ GARAM

🚀 GARAM Bot Test
```

## 5. 사용법

### Python 코드에서

```python
from utils.telegram_bot import send_telegram

# 정보 알림
send_telegram("시스템 시작 완료", 'info')

# 경고 알림
send_telegram("Dashboard 재시작 중", 'warning')

# 긴급 알림
send_telegram("수동 개입 필요!", 'critical')
```

### 명령 수신

Telegram 앱에서 Bot에게 전송:

- `/status` - 시스템 상태 확인
- `/kill` - 긴급 거래 중단
- `/restart` - Dashboard 재시작
- `/help` - 도움말

## 6. Auto-Start 통합

### auto_start.py 수정

```python
# 상단에 추가
from utils.telegram_bot import send_telegram

# 시작 시 알림
send_telegram("🚀 GARAM 자동 시작 시작", 'info')

# 성공 시
send_telegram("✅ GARAM 자동 시작 완료", 'success')

# 실패 시
send_telegram("❌ 자동 시작 실패", 'critical')
```

### Watchdog 통합

```python
from utils.telegram_bot import send_telegram

# Dashboard 다운 감지
send_telegram("⚠️ Dashboard 다운 감지\n재시작 중...", 'warning')

# 재시작 성공
send_telegram("✅ Dashboard 재시작 성공", 'success')
```

## 7. 승인 시스템

### 승인 요청

```python
from utils.telegram_bot import get_telegram_bot

bot = get_telegram_bot()

# 승인 요청 전송
approval_id = bot.request_approval(
    action="stop_trading",
    reason="MDD -20% 초과",
    timeout=300  # 5분
)

# Telegram에서 승인/거부 버튼 표시
```

### Telegram에서 응답

사용자가 버튼 클릭:

- ✅ 승인 → 액션 실행
- ❌ 거부 → 액션 취소

## 8. Kill Switch

### 긴급 중단

Telegram에서 `/kill` 입력 시:

```
1. 모든 열린 포지션 청산
2. 새 거래 중단
3. 수동 모드 전환
```

### 안전 장치

Kill Switch는 즉시 실행되며:

- 모든 주문 취소
- 포지션 강제 청산
- Turbo 비활성화
- Base 거래 중단

## 9. 문제 해결

### Bot이 응답 없음

1. Bot Token 확인
2. Chat ID 확인
3. Bot과 대화 시작 (`/start`)
4. 네트워크 연결 확인

### 환경 변수 인식 안 됨

PowerShell 재시작:

```powershell
# 현재 세션에서만 설정
$env:GARAM_TELEGRAM_BOT_TOKEN="YOUR_TOKEN"
$env:GARAM_TELEGRAM_CHAT_ID="YOUR_CHAT_ID"
```

### 한글 깨짐

Telegram은 UTF-8 지원, 문제 없음

## 10. 보안

### Token 보호

- ⚠️ GitHub에 업로드 금지
- ⚠️ 코드에 하드코딩 금지
- ✅ 환경 변수만 사용

### Bot 권한

- Bot은 사용자와의 1:1 대화만 가능
- 그룹에 초대하지 않는 한 안전

## 11. 고급 기능 (향후)

### 실시간 상태 모니터링

```python
# 매 5분마다 상태 전송
while True:
    status = get_system_status()
    send_telegram(f"시스템 정상\nEquity: {status['equity']}", 'info')
    time.sleep(300)
```

### 거래 알림

```python
# 포지션 진입/청산 시
send_telegram(f"📈 {symbol} 진입\n가격: {price}", 'info')
send_telegram(f"📉 {symbol} 청산\nPnL: {pnl}", 'success')
```

### 승인 시간제한

```python
# 5분 내 응답 없으면 자동 거부
approval_id = bot.request_approval(
    action="emergency_exit",
    reason="MDD 초과",
    timeout=300
)
```

---

**Status**: 📝 설정 가이드  
**Required**: Bot Token + Chat ID  
**Time**: ~10분
