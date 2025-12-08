# 백엔드 ngrok 터널 시작 가이드

백엔드 서버는 실행 중이지만, ngrok 터널이 없어서 외부에서 접속할 수 없습니다.

## 빠른 해결 방법

### 방법 1: 새 터미널에서 수동 시작 (권장)

새 PowerShell 터미널을 열고 다음 명령어를 실행하세요:

```powershell
ngrok http 8000
```

터미널에 다음과 같은 출력이 표시됩니다:

```
Forwarding   https://[랜덤-이름].ngrok-free.dev -> http://localhost:8000
```

이 URL이 백엔드 API URL입니다.

### 방법 2: 기존 ngrok 프로세스 확인 및 종료 후 재시작

1. **실행 중인 ngrok 프로세스 확인:**
   ```powershell
   Get-Process | Where-Object {$_.ProcessName -like "*ngrok*"}
   ```

2. **모든 ngrok 프로세스 종료:**
   ```powershell
   taskkill /F /IM ngrok.exe
   ```

3. **백엔드 터널 시작 (터미널 1):**
   ```powershell
   ngrok http 8000
   ```

4. **프론트엔드 터널 시작 (터미널 2):**
   ```powershell
   ngrok http 3000
   ```

## 백엔드 서버 확인

백엔드 서버가 실행 중인지 확인:

```powershell
# 로컬에서 테스트
Invoke-WebRequest -Uri "http://localhost:8000/api/stats"
```

정상 응답이 오면 백엔드는 실행 중입니다.

## 프론트엔드 환경 변수 설정

백엔드 ngrok URL을 얻은 후, `frontend/.env` 파일을 생성/수정:

```env
REACT_APP_API_URL=https://[백엔드-ngrok-URL]/api
```

예시:
```env
REACT_APP_API_URL=https://nannette-pretentative-lannie.ngrok-free.dev/api
```

## 현재 상태 확인

ngrok 웹 인터페이스에서 확인:
- http://127.0.0.1:4040 접속
- 실행 중인 터널 목록 확인
- 각 터널의 Public URL 확인

## 문제 해결

### "endpoint is already online" 오류

같은 엔드포인트가 이미 사용 중일 때:

```powershell
# 모든 ngrok 프로세스 종료
taskkill /F /IM ngrok.exe

# 잠시 대기 후 다시 시작
Start-Sleep -Seconds 2
ngrok http 8000
```

### 백엔드 서버가 응답하지 않음

백엔드 서버가 실행 중인지 확인:

```powershell
# 서버 실행 (프로젝트 루트에서)
.\venv\Scripts\python.exe run_server.py
```

또는:

```powershell
.\venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000
```

## 완전한 설정 예시

### 터미널 1: 백엔드 서버
```powershell
cd C:\Users\qlcke\projects\hourly-pulse
.\venv\Scripts\python.exe run_server.py
```

### 터미널 2: 백엔드 ngrok
```powershell
ngrok http 8000
```

### 터미널 3: 프론트엔드 서버
```powershell
cd C:\Users\qlcke\projects\hourly-pulse\frontend
npm start
```

### 터미널 4: 프론트엔드 ngrok
```powershell
ngrok http 3000
```

각 터미널에 표시되는 URL을 기록해두세요!

