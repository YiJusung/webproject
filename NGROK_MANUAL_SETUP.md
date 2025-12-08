# ngrok 수동 설정 가이드

자동 스크립트가 작동하지 않는 경우, 수동으로 ngrok 터널을 설정할 수 있습니다.

## 방법 1: 별도 터미널에서 실행 (가장 간단) ⭐

### 터미널 1: 백엔드 터널
```powershell
ngrok http 8000
```

출력 예시:
```
Forwarding   https://abc123.ngrok-free.dev -> http://localhost:8000
```

### 터미널 2: 프론트엔드 터널
```powershell
ngrok http 3000
```

출력 예시:
```
Forwarding   https://xyz789.ngrok-free.dev -> http://localhost:3000
```

### 프론트엔드 환경 변수 설정

`frontend/.env` 파일을 생성하고 다음을 추가:

```env
REACT_APP_API_URL=https://abc123.ngrok-free.dev/api
```

**주의**: `abc123.ngrok-free.dev`를 실제 백엔드 ngrok URL로 변경하세요.

## 방법 2: ngrok config 파일 사용 (고급)

여러 터널을 하나의 ngrok 인스턴스로 관리할 수 있습니다.

### 1. ngrok config 파일 위치 확인

Windows:
```
C:\Users\<사용자명>\AppData\Local\ngrok\ngrok.yml
```

### 2. config 파일 편집

`ngrok.yml` 파일에 다음 내용 추가:

```yaml
version: "2"
authtoken: YOUR_AUTH_TOKEN
tunnels:
  backend:
    addr: 8000
    proto: http
  frontend:
    addr: 3000
    proto: http
```

### 3. ngrok 시작

```powershell
ngrok start --all
```

또는 특정 터널만 시작:

```powershell
ngrok start backend frontend
```

### 4. 터널 URL 확인

웹 브라우저에서 접속:
```
http://127.0.0.1:4040
```

또는 API로 확인:
```powershell
curl http://127.0.0.1:4040/api/tunnels
```

## 방법 3: ngrok 웹 인터페이스 사용

1. **ngrok 시작**:
   ```powershell
   ngrok http 8000
   ```

2. **웹 브라우저에서 접속**:
   ```
   http://127.0.0.1:4040
   ```

3. **터널 정보 확인**:
   - Public URL 확인
   - 요청/응답 로그 확인
   - 재실행 기능 사용

## 문제 해결

### 문제 1: "endpoint is already online" 오류

**원인**: 같은 엔드포인트가 이미 실행 중

**해결**:
1. 실행 중인 ngrok 프로세스 종료:
   ```powershell
   taskkill /F /IM ngrok.exe
   ```
2. 잠시 대기 후 다시 시작

### 문제 2: URL을 가져올 수 없음

**원인**: ngrok API(포트 4040)에 접근할 수 없음

**해결**:
1. ngrok이 정상적으로 시작되었는지 확인
2. 웹 브라우저에서 `http://127.0.0.1:4040` 접속 시도
3. 방화벽이 4040 포트를 차단하지 않는지 확인

### 문제 3: 여러 터널을 동시에 실행할 수 없음

**원인**: ngrok 무료 플랜은 기본적으로 하나의 터널만 지원

**해결**:
- 방법 1: 별도 터미널에서 각각 실행 (권장)
- 방법 2: ngrok config 파일 사용
- 방법 3: ngrok 유료 플랜 사용 (여러 터널 동시 실행)

## 추천 방법

**개발/테스트 환경**: 방법 1 (별도 터미널) - 가장 간단하고 안정적

**프로덕션 환경**: 클라우드 배포 (Vercel, Railway 등) - ngrok은 개발용으로만 권장

## 빠른 시작 (복사해서 사용)

### 터미널 1 (백엔드):
```powershell
cd C:\Users\qlcke\projects\hourly-pulse
ngrok http 8000
```

### 터미널 2 (프론트엔드):
```powershell
cd C:\Users\qlcke\projects\hourly-pulse
ngrok http 3000
```

### 터미널 3 (프론트엔드 환경 변수 설정):
```powershell
cd C:\Users\qlcke\projects\hourly-pulse\frontend
# 백엔드 ngrok URL을 복사한 후
echo REACT_APP_API_URL=https://[백엔드_ngrok_URL]/api > .env
```

각 터미널에 표시되는 URL을 기록해두세요!

