# 📊 TrendPulse

실시간 이슈 트렌드 분석 플랫폼 - 다양한 소스에서 데이터를 수집하고 AI로 분석하여 트렌드를 파악합니다.

## ✨ 주요 기능

- 🔄 **자동 데이터 수집**: Reddit, 뉴스, GitHub, YouTube에서 5분마다 자동 수집
- 🤖 **AI 분석**: Google Gemini API를 활용한 심층 분석
- 📈 **관심도 점수**: 조회수, 좋아요, 댓글 등을 기반으로 한 관심도 계산
- 🏆 **트렌드 랭킹**: 관심도 점수 기반 실시간 랭킹
- 🔥 **급상승 트렌드**: 급격히 상승한 트렌드 자동 감지
- 🌐 **다국어 지원**: 한국어/영어 지원
- 🌙 **다크 모드**: 라이트/다크 모드 전환
- 📱 **반응형 디자인**: 모바일, 태블릿, 데스크톱 지원

## 🏗️ 기술 스택

### 백엔드
- **FastAPI**: Python 웹 프레임워크
- **PostgreSQL**: 데이터베이스
- **SQLAlchemy**: ORM
- **APScheduler**: 비동기 작업 스케줄러
- **Google Gemini API**: AI 분석
- **httpx**: 비동기 HTTP 클라이언트

### 프론트엔드
- **React**: UI 라이브러리
- **Tailwind CSS**: 스타일링
- **Axios**: HTTP 클라이언트
- **Recharts**: 차트 라이브러리
- **Lucide React**: 아이콘

## 📋 사전 요구사항

- Python 3.10 이상
- Node.js 16 이상
- PostgreSQL 12 이상
- Google Gemini API Key
- (선택) ngrok (인터넷 접속용)

## 🚀 빠른 시작

### 1. 저장소 클론

```bash
git clone <repository-url>
cd hourly-pulse
```

### 2. 백엔드 설정

#### 가상 환경 생성 및 활성화

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 의존성 설치

```bash
pip install -r requirements.txt
```

#### 환경 변수 설정

`.env` 파일을 프로젝트 루트에 생성:

```env
# 데이터베이스
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/hourly_pulse

# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
```

#### 데이터베이스 초기화

```bash
python -m app.core.database
```

또는 서버 실행 시 자동으로 초기화됩니다.

#### 서버 실행

```bash
# Windows
.\venv\Scripts\python.exe run_server.py

# 또는
.\venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000
```

### 3. 프론트엔드 설정

#### 의존성 설치

```bash
cd frontend
npm install
```

#### 환경 변수 설정 (선택사항)

`frontend/.env` 파일 생성:

```env
REACT_APP_API_URL=http://localhost:8000/api
```

#### 개발 서버 실행

```bash
npm start
```

웹사이트가 http://localhost:3000 에서 실행됩니다.

## 📖 상세 가이드

### 데이터 수집

- **주기**: 5분마다 자동 수집
- **소스**: Reddit, 뉴스 RSS, GitHub, YouTube
- **수집량**: 각 소스별 대량 수집 (4K RPM 활용)

자세한 내용은 [DATA_FLOW.md](DATA_FLOW.md) 참고

### AI 분석

- **모델**: Google Gemini API
- **분석 내용**: What, Why Now, Context
- **주기**: 데이터 수집 후 자동 분석

### 관심도 점수 계산

- **YouTube**: 실제 조회수 사용
- **Reddit**: upvotes × 15 + comments × 5
- **GitHub**: stars × 20 + forks × 10 + watchers × 3
- **News**: 휴리스틱 점수 또는 댓글 기반 추정

자세한 내용은 [INTEREST_SCORE_ANALYSIS.md](INTEREST_SCORE_ANALYSIS.md) 참고

### 네트워크 접속

#### 로컬 네트워크 접속

같은 Wi-Fi/LAN에 연결된 기기에서 접속:

1. 프론트엔드 서버를 네트워크 모드로 실행:
   ```bash
   cd frontend
   npm run start:network
   ```

2. PC의 IP 주소 확인 후 접속:
   ```
   http://[PC-IP-주소]:3000
   ```

자세한 내용은 [NETWORK_ACCESS_GUIDE.md](NETWORK_ACCESS_GUIDE.md) 참고

#### 인터넷 접속 (ngrok)

인터넷 어디서나 접속:

1. ngrok 설치 및 인증:
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

2. 백엔드 터널 시작:
   ```bash
   ngrok http 8000
   ```

3. 프론트엔드 터널 시작 (새 터미널):
   ```bash
   ngrok http 3000
   ```

4. 프론트엔드 환경 변수 설정:
   ```env
   REACT_APP_API_URL=https://[백엔드-ngrok-URL]/api
   ```

자세한 내용은 [INTERNET_ACCESS_GUIDE.md](INTERNET_ACCESS_GUIDE.md) 참고

## 📁 프로젝트 구조

```
hourly-pulse/
├── app/                    # 백엔드 애플리케이션
│   ├── api/               # API 엔드포인트
│   ├── core/              # 데이터베이스 설정
│   ├── services/          # 비즈니스 로직
│   │   ├── ai_analyzer.py      # AI 분석
│   │   ├── ranking.py          # 랭킹 계산
│   │   ├── storage.py           # 데이터 저장
│   │   └── unified_collector.py # 데이터 수집
│   └── main.py            # FastAPI 앱
├── frontend/              # 프론트엔드 애플리케이션
│   ├── src/
│   │   ├── components/    # React 컴포넌트
│   │   ├── contexts/      # React Context
│   │   └── utils/         # 유틸리티
│   └── package.json
├── requirements.txt       # Python 의존성
└── README.md             # 이 파일
```

## 🔧 주요 설정

### 데이터 수집 간격 변경

`app/main.py`에서 수정:

```python
scheduler.add_job(
    job_collection_task, 
    "interval", 
    minutes=5,  # 여기서 간격 변경
    ...
)
```

### AI 분석 설정

`app/services/ai_analyzer.py`에서 모델, 토큰 제한 등 설정 가능

### 관심도 점수 가중치 조정

`app/services/ranking.py`의 `calculate_item_interest_score()` 함수에서 조정

## 🐛 문제 해결

### 백엔드 서버가 시작되지 않음

- PostgreSQL이 실행 중인지 확인
- `.env` 파일의 `DATABASE_URL` 확인
- 포트 8000이 사용 중이 아닌지 확인

### 프론트엔드에서 데이터가 표시되지 않음

- 백엔드 서버가 실행 중인지 확인
- 브라우저 콘솔에서 오류 확인
- `frontend/.env`의 `REACT_APP_API_URL` 확인
- CORS 설정 확인 (`app/main.py`)

### ngrok 연결 오류

- ngrok 인증 토큰이 올바르게 설정되었는지 확인
- 기존 ngrok 프로세스 종료 후 재시작
- 자세한 내용은 [NGROK_SETUP.md](NGROK_SETUP.md) 참고

## 📚 추가 문서

- [DATA_FLOW.md](DATA_FLOW.md) - 데이터 수집 및 처리 흐름
- [NETWORK_ACCESS_GUIDE.md](NETWORK_ACCESS_GUIDE.md) - 로컬 네트워크 접속 가이드
- [INTERNET_ACCESS_GUIDE.md](INTERNET_ACCESS_GUIDE.md) - 인터넷 접속 가이드 (ngrok)
- [NGROK_SETUP.md](NGROK_SETUP.md) - ngrok 설정 가이드
- [INTEREST_SCORE_ANALYSIS.md](INTEREST_SCORE_ANALYSIS.md) - 관심도 점수 계산 방법

## 🤝 기여

이슈 리포트 및 풀 리퀘스트를 환영합니다!

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 🙏 감사의 말

- Google Gemini API
- FastAPI 커뮤니티
- React 커뮤니티

---

**TrendPulse v0.1.0** - 실시간 이슈 트렌드 분석 플랫폼

