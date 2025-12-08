# 프론트엔드 설정 가이드

## 1. 수집 간격 변경 완료 ✅

수집 간격이 **1분**으로 변경되었습니다.

## 2. React 웹사이트 실행 방법

### 2.1 의존성 설치

```bash
cd frontend
npm install
```

### 2.2 개발 서버 실행

```bash
npm start
```

웹사이트가 http://localhost:3000 에서 실행됩니다.

### 2.3 백엔드 서버 실행 (별도 터미널)

```bash
# 프로젝트 루트에서
.\venv\Scripts\uvicorn.exe app.main:app --reload
```

## 3. 웹사이트 기능

- 📊 **통계 대시보드**: 총 수집 데이터, 분석 결과, 랭킹 수 표시
- 🏆 **이슈 랭킹**: 중요도 점수와 함께 상위 이슈 표시
- 🤖 **AI 분석 결과**: 토픽, 요약, 키워드, 감정 분석 표시
- 📰 **최근 수집 데이터**: 최신 수집된 뉴스, Reddit, GitHub 등 표시
- 🔄 **자동 새로고침**: 30초마다 자동으로 데이터 업데이트

## 4. 파일 구조

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── App.js          # 메인 앱 컴포넌트
│   ├── App.css
│   ├── index.js
│   ├── index.css
│   └── components/
│       ├── Stats.js       # 통계 컴포넌트
│       ├── Rankings.js    # 랭킹 컴포넌트
│       ├── RecentData.js  # 최근 데이터 컴포넌트
│       └── Analysis.js    # 분석 결과 컴포넌트
├── package.json
└── README.md
```

## 5. 환경 변수 (선택사항)

`frontend/.env` 파일을 생성하여 API URL을 변경할 수 있습니다:

```
REACT_APP_API_URL=http://localhost:8000/api
```

## 6. 문제 해결

### CORS 오류
- 백엔드 서버가 실행 중인지 확인
- `app/main.py`에 CORS 미들웨어가 추가되어 있는지 확인

### 데이터가 표시되지 않음
- 백엔드 API가 정상 작동하는지 확인: http://localhost:8000/api/stats
- 브라우저 콘솔에서 오류 확인




