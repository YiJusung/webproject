# 다른 PC/모바일에서 웹사이트 접속 가이드

## 현재 설정 상태

### 백엔드 서버
- ✅ 이미 외부 접속 가능: `host="0.0.0.0"` 설정됨
- 포트: `8000`

### 프론트엔드 서버
- ✅ 외부 접속 가능하도록 설정됨
- 포트: `3000` (기본값)
- API URL 자동 감지: 접속한 IP 주소를 자동으로 사용

## 빠른 시작

### 1단계: PC의 로컬 IP 주소 확인

**Windows PowerShell:**
```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*"}
```

**찾아야 할 IP:**
- `192.168.x.x` 또는 `10.x.x.x` 형태의 IP 주소
- 예: `192.168.35.56` (현재 PC의 IP)

### 2단계: 프론트엔드 서버 외부 접속 허용

**방법 1: npm 스크립트 사용 (권장)**
```bash
cd frontend
npm run start:network
```

**방법 2: 직접 실행**
```bash
cd frontend
set HOST=0.0.0.0
set DANGEROUSLY_DISABLE_HOST_CHECK=true
npm start
```

### 3단계: 방화벽 설정

**PowerShell로 자동 설정 (관리자 권한 필요):**
```powershell
New-NetFirewallRule -DisplayName "TrendPulse Frontend" -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "TrendPulse Backend" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

**또는 수동 설정:**
1. Windows 보안 → 방화벽 및 네트워크 보호
2. 고급 설정
3. 인바운드 규칙 → 새 규칙
4. 포트 선택 → TCP → 특정 로컬 포트: `3000, 8000`
5. 연결 허용 → 모든 프로필 선택

### 4단계: 다른 기기에서 접속

**같은 네트워크(Wi-Fi)에 연결된 기기에서:**
```
http://192.168.35.56:3000
```
(192.168.35.56을 실제 PC의 IP 주소로 변경)

## 자동 API URL 감지

프론트엔드가 자동으로 현재 접속한 호스트의 IP를 감지하여 API URL을 설정합니다:

- `localhost`로 접속 → `http://localhost:8000/api` 사용
- `192.168.35.56`로 접속 → `http://192.168.35.56:8000/api` 사용

**수동 설정이 필요한 경우:**
```bash
# frontend/.env 파일 생성
REACT_APP_API_URL=http://192.168.35.56:8000/api
```

## 주의사항

1. **같은 네트워크 필수**: PC와 접속 기기가 같은 Wi-Fi/랜에 연결되어 있어야 함
2. **IP 주소 변경**: PC를 재시작하거나 네트워크를 변경하면 IP 주소가 바뀔 수 있음
3. **보안**: 로컬 네트워크에서만 접속 가능 (인터넷 공개 아님)
4. **서버 실행**: 백엔드와 프론트엔드 서버가 모두 실행 중이어야 함

## 인터넷에서 접속하려면

인터넷에서 접속하려면:
1. **포트 포워딩**: 라우터에서 포트 3000, 8000을 PC로 포워딩
2. **공인 IP 주소**: 라우터의 공인 IP 주소 확인
3. **도메인/DDNS**: 동적 IP를 도메인으로 연결 (선택)
4. **클라우드 배포**: AWS, Azure, Heroku 등에 배포 (권장)

## 빠른 테스트

1. PC에서 백엔드 서버 실행: `python run_server.py`
2. PC에서 프론트엔드 서버 실행: `cd frontend && npm run start:network`
3. 같은 네트워크의 다른 기기에서 브라우저 열기
4. `http://[PC의IP주소]:3000` 입력 (예: `http://192.168.35.56:3000`)
5. 접속 확인

## 문제 해결

### 접속이 안 될 때

1. **방화벽 확인**: Windows 방화벽에서 포트 3000, 8000 허용 확인
2. **네트워크 확인**: 같은 Wi-Fi/랜에 연결되어 있는지 확인
3. **IP 주소 확인**: PC의 IP 주소가 변경되지 않았는지 확인
4. **서버 실행 확인**: 백엔드와 프론트엔드 서버가 모두 실행 중인지 확인

### CORS 오류가 발생할 때

백엔드 서버의 CORS 설정이 이미 모든 origin을 허용하도록 설정되어 있습니다.
만약 문제가 발생하면 `app/main.py`의 CORS 설정을 확인하세요.
