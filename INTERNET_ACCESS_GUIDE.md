# 인터넷을 통한 웹사이트 접속 가이드

같은 Wi-Fi/랜에 연결되지 않고도 인터넷 어디서나 접속할 수 있는 방법들입니다.

## 방법 1: ngrok 사용 (가장 간단, 추천) ⭐

### 장점
- ✅ 설정이 매우 간단
- ✅ 무료 플랜 제공
- ✅ HTTPS 자동 제공
- ✅ 즉시 사용 가능
- ✅ 자동 스크립트 제공

### 단점
- ⚠️ 무료 플랜은 URL이 매번 변경됨 (유료 플랜은 고정 도메인)
- ⚠️ 무료 플랜은 연결 시간 제한 있음

### 빠른 시작

#### 1단계: ngrok 설치 및 인증

**Windows:**
```powershell
# Chocolatey 사용 (관리자 권한)
choco install ngrok

# 또는 직접 다운로드
# https://ngrok.com/download
```

**ngrok 계정 생성 및 인증:**
1. https://ngrok.com 에서 무료 계정 생성
2. 대시보드에서 인증 토큰 복사
3. PowerShell에서 실행:
```powershell
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

#### 2단계: 자동 스크립트 사용 (권장)

**백엔드와 프론트엔드 터널 자동 생성:**
```bash
python start_ngrok.py
```

이 스크립트는:
- 백엔드(포트 8000)와 프론트엔드(포트 3000) 터널을 자동으로 생성
- 생성된 URL을 표시
- 환경 변수 설정 방법 안내

#### 3단계: 수동 설정 (선택)

**백엔드 터널 (터미널 1):**
```bash
ngrok http 8000
```
- 생성된 URL 예: `https://abc123.ngrok.io`
- 이 URL을 백엔드 API URL로 사용

**프론트엔드 터널 (터미널 2):**
```bash
ngrok http 3000
```
- 생성된 URL 예: `https://xyz789.ngrok.io`
- 이 URL을 다른 기기에서 접속

**프론트엔드 환경 변수 설정:**
```bash
# frontend/.env 파일 생성
REACT_APP_API_URL=https://abc123.ngrok.io/api
```

#### 4단계: 다른 기기에서 접속

인터넷 어디서나 접속 가능:
```
https://xyz789.ngrok.io
```

## 방법 2: Cloudflare Tunnel (Cloudflared)

### 장점
- ✅ 완전 무료
- ✅ 고정 도메인 가능
- ✅ 빠른 속도
- ✅ 무제한 대역폭

### 단점
- ⚠️ 설정이 다소 복잡

### 설정 방법

1. **Cloudflared 설치**
   ```powershell
   choco install cloudflared
   ```

2. **터널 생성**
   ```bash
   # 프론트엔드
   cloudflared tunnel --url http://localhost:3000
   
   # 백엔드 (별도 터미널)
   cloudflared tunnel --url http://localhost:8000
   ```

## 방법 3: localtunnel

### 장점
- ✅ npm으로 간단 설치
- ✅ 무료

### 단점
- ⚠️ URL이 매번 변경됨
- ⚠️ 안정성이 낮을 수 있음

### 설정 방법

```bash
# 설치
npm install -g localtunnel

# 프론트엔드
lt --port 3000

# 백엔드 (별도 터미널)
lt --port 8000
```

## 방법 4: 포트 포워딩 + 공인 IP

### 장점
- ✅ 자체 서버 완전 제어
- ✅ 고정 IP 사용 가능

### 단점
- ⚠️ 라우터 설정 필요
- ⚠️ 보안 위험 (직접 인터넷 노출)
- ⚠️ 공인 IP 필요 (일부 ISP는 제공 안 함)

### 설정 방법

1. **라우터 관리 페이지 접속** (보통 192.168.1.1)
2. **포트 포워딩 설정**
   - 포트 3000 → PC의 로컬 IP:3000
   - 포트 8000 → PC의 로컬 IP:8000
3. **공인 IP 주소 확인**
   - https://whatismyipaddress.com
4. **다른 기기에서 접속**
   ```
   http://[공인IP주소]:3000
   ```

## 방법 5: 클라우드 배포 (프로덕션 권장)

### 옵션

#### 프론트엔드
- **Vercel**: https://vercel.com (무료, 자동 HTTPS)
- **Netlify**: https://netlify.com (무료, 자동 HTTPS)

#### 백엔드
- **Railway**: https://railway.app (무료 플랜)
- **Render**: https://render.com (무료 플랜)
- **Fly.io**: https://fly.io (무료 플랜)

#### 전체 스택
- **AWS**: EC2, Elastic Beanstalk
- **Azure**: App Service
- **Google Cloud**: Cloud Run

### 장점
- ✅ 안정적
- ✅ 고정 도메인
- ✅ HTTPS 자동
- ✅ 24/7 운영
- ✅ 자동 배포

### 단점
- ⚠️ 설정 시간 필요
- ⚠️ 일부 서비스는 무료 플랜 제한

## 추천 순서

1. **개발/테스트**: ngrok (가장 빠르고 간단)
2. **프로덕션**: 클라우드 배포 (Vercel + Railway)

## ngrok 자동 스크립트 사용법

프로젝트에 포함된 `start_ngrok.py` 스크립트를 사용하면 자동으로 터널을 생성합니다:

```bash
python start_ngrok.py
```

이 스크립트는:
- ✅ 백엔드와 프론트엔드 터널을 자동으로 생성
- ✅ 생성된 URL을 표시
- ✅ 환경 변수 설정 방법 안내

## 주의사항

1. **보안**: ngrok 무료 플랜은 공개 URL이므로 누구나 접속 가능
2. **성능**: 무료 플랜은 대역폭 제한이 있을 수 있음
3. **안정성**: 무료 플랜은 연결 시간 제한이 있을 수 있음
4. **프로덕션**: 프로덕션 환경에서는 클라우드 배포를 권장
