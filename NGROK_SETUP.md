# ngrok 인증 토큰 설정 가이드

## 문제 해결

현재 ngrok 인증 토큰이 올바르지 않거나 설정되지 않아 오류가 발생하고 있습니다.

## 해결 방법

### 1단계: ngrok 계정 생성 및 인증 토큰 가져오기

1. **ngrok 대시보드 접속**
   - https://dashboard.ngrok.com/get-started/your-authtoken
   - 또는 https://dashboard.ngrok.com 에서 로그인 후 "Your Authtoken" 메뉴

2. **인증 토큰 복사**
   - 대시보드에서 표시된 인증 토큰을 복사합니다
   - 형식: `2abc...` (약 40자 정도의 문자열)
   - ⚠️ **주의**: `cr_`로 시작하는 토큰은 올바른 형식이 아닙니다

### 2단계: 인증 토큰 설정

PowerShell에서 다음 명령어를 실행하세요:

```powershell
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

예시:
```powershell
ngrok config add-authtoken 2abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
```

### 3단계: 설정 확인

인증 토큰이 올바르게 설정되었는지 확인:

```powershell
ngrok config check
```

정상적으로 설정되었다면 오류 없이 실행됩니다.

### 4단계: 터널 시작

인증 토큰 설정이 완료되면 다시 스크립트를 실행:

```powershell
python start_ngrok.py
```

## 자주 발생하는 오류

### 오류 1: "authentication failed: The authtoken you specified does not look like a proper ngrok authtoken"

**원인**: 
- 잘못된 형식의 토큰 사용
- 토큰이 설정되지 않음

**해결**:
1. ngrok 대시보드에서 올바른 토큰을 다시 복사
2. `ngrok config add-authtoken` 명령으로 다시 설정

### 오류 2: "ERR_NGROK_105"

**원인**: 인증 토큰이 유효하지 않음

**해결**:
- https://ngrok.com/docs/errors/err_ngrok_105 참고
- 대시보드에서 새로운 토큰을 생성하여 설정

### 오류 3: "ngrok API 조회 실패: HTTPConnectionPool (host='127.0.0.1', port=4040)"

**원인**: 
- ngrok이 실행되지 않음
- 인증 토큰이 설정되지 않아 ngrok이 시작되지 않음

**해결**:
1. 먼저 인증 토큰을 올바르게 설정
2. 그 다음 스크립트 실행

## 수동 터널 생성 (스크립트 대신)

스크립트가 작동하지 않는 경우, 수동으로 터널을 생성할 수 있습니다:

### 터미널 1: 백엔드 터널
```powershell
ngrok http 8000
```

### 터미널 2: 프론트엔드 터널
```powershell
ngrok http 3000
```

각 터미널에 표시되는 URL을 사용하세요.

## 추가 도움말

- ngrok 공식 문서: https://ngrok.com/docs
- 오류 코드 참고: https://ngrok.com/docs/errors
- 대시보드: https://dashboard.ngrok.com

