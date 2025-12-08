# ngrok 빠른 시작 가이드

## 오류 해결: "endpoint is already online"

이 오류는 같은 엔드포인트가 이미 사용 중일 때 발생합니다.

## 해결 방법

### 1단계: 기존 ngrok 프로세스 종료

PowerShell에서 실행:

```powershell
# 모든 ngrok 프로세스 종료
Get-Process | Where-Object {$_.ProcessName -like "*ngrok*"} | Stop-Process -Force
```

또는:

```powershell
taskkill /F /IM ngrok.exe
```

### 2단계: 잠시 대기

```powershell
Start-Sleep -Seconds 2
```

### 3단계: 새로 시작

**터미널 1: 백엔드 터널**
```powershell
ngrok http 8000
```

**터미널 2: 프론트엔드 터널**
```powershell
ngrok http 3000
```

## 완전한 설정 순서

### 1. 모든 ngrok 프로세스 종료
```powershell
taskkill /F /IM ngrok.exe
```

### 2. 백엔드 서버 확인/시작
```powershell
cd C:\Users\qlcke\projects\hourly-pulse
.\venv\Scripts\python.exe run_server.py
```

### 3. 새 터미널: 백엔드 ngrok
```powershell
ngrok http 8000
```
→ 백엔드 URL 복사 (예: `https://abc123.ngrok-free.dev`)

### 4. 새 터미널: 프론트엔드 서버
```powershell
cd C:\Users\qlcke\projects\hourly-pulse\frontend
npm start
```

### 5. 새 터미널: 프론트엔드 ngrok
```powershell
ngrok http 3000
```
→ 프론트엔드 URL 복사 (예: `https://xyz789.ngrok-free.dev`)

### 6. 프론트엔드 환경 변수 설정

`frontend/.env` 파일 생성/수정:

```env
REACT_APP_API_URL=https://[백엔드-ngrok-URL]/api
```

예시:
```env
REACT_APP_API_URL=https://abc123.ngrok-free.dev/api
```

## 문제 해결

### "endpoint is already online" 오류가 계속 발생

1. **모든 ngrok 프로세스 강제 종료:**
   ```powershell
   taskkill /F /IM ngrok.exe
   ```

2. **ngrok 웹 인터페이스 확인:**
   - http://127.0.0.1:4040 접속
   - 실행 중인 터널이 있는지 확인
   - 있으면 브라우저에서 종료

3. **잠시 대기 후 재시작:**
   ```powershell
   Start-Sleep -Seconds 5
   ngrok http 8000
   ```

### ngrok이 시작되지 않음

1. **ngrok 설치 확인:**
   ```powershell
   ngrok version
   ```

2. **인증 토큰 확인:**
   ```powershell
   ngrok config check
   ```

3. **인증 토큰 재설정:**
   - https://dashboard.ngrok.com/get-started/your-authtoken
   - 토큰 복사 후:
   ```powershell
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

## 한 번에 정리하는 스크립트

PowerShell에서 실행:

```powershell
# 모든 ngrok 프로세스 종료
taskkill /F /IM ngrok.exe 2>$null

# 잠시 대기
Start-Sleep -Seconds 2

Write-Host "✅ 정리 완료! 이제 새로 시작할 수 있습니다."
Write-Host "`n백엔드: ngrok http 8000"
Write-Host "프론트엔드: ngrok http 3000"
```

## 추천: 별도 터미널 사용

ngrok은 각 터미널에서 하나씩 실행하는 것이 가장 안정적입니다:

- **터미널 1**: 백엔드 서버
- **터미널 2**: 백엔드 ngrok
- **터미널 3**: 프론트엔드 서버  
- **터미널 4**: 프론트엔드 ngrok

각 터미널을 닫지 않고 유지하세요!

