export const translations = {
  ko: {
    // 헤더
    title: '📊 TrendPulse',
    subtitle: '실시간 이슈 트렌드 분석',
    lastUpdate: '마지막 업데이트',
    refresh: '🔄 새로고침',
    refreshing: '새로고침 중...',
    
    // 통계
    totalCollected: '총 수집 데이터',
    totalAnalysis: 'AI 분석 결과',
    totalRankings: '이슈 랭킹',
    sourceStats: '소스별 통계',
    
    // 이슈 랭킹
    issueRanking: '🏆 이슈 랭킹',
    noRankingData: '랭킹 데이터가 없습니다.',
    score: '점수',
    mentions: '언급',
    sources: '소스',
    issueContent: '📋 이슈 내용',
    what: '📋 무엇인가',
    whyNow: '⏰ 왜 지금',
    context: '🌐 맥락',
    
    // AI 분석
    aiAnalysis: '🤖 AI 분석 결과',
    noAnalysisData: '분석 결과가 없습니다.',
    importance: '중요도',
    sentiment: '감정',
    
    // 최근 데이터
    recentData: '📰 최근 수집 데이터',
    noRecentData: '수집된 데이터가 없습니다.',
    
    // 에러
    errorLoading: '데이터를 불러오는데 실패했습니다. 서버가 실행 중인지 확인해주세요.',
    loading: '데이터를 불러오는 중...',
    
    // 푸터
    footer: 'TrendPulse v0.1.0 | 데이터 수집 간격: 5분',
    
    // 언어 선택
    language: '언어',
    korean: '한국어',
    english: 'English',
    
    // 감정
    positive: '긍정',
    negative: '부정',
    neutral: '중립',
    
    // 기타
    viewOriginal: '원문 보기 →',
    expand: '▼ 더보기',
    collapse: '▲ 접기',
    items: '개',
    
    // Stats
    totalTrends: '총 트렌드',
    totalInterest: '총 관심도',
    realtimeUpdate: '실시간 갱신',
    every5Minutes: '5분마다',
    
    // Surge Trends
    surgeTrends: '🔥 급상승 트렌드',
    surgeTrendsDesc: '최근 15분 내 급격히 상승한 트렌드',
    rankChange: '순위',
    interestIncrease: '배 증가',
    
    // Chart
    trendChart: '트렌드 추이',
    lastHour: '최근 1시간 (5분 간격)',
    
    // Trend Card
    interest: '관심도',
    changeRate: '변화율',
    source: '출처',
    
    // Categories
    all: '전체',
    news: '뉴스',
    social: '소셜',
    tech: '기술',
    entertainment: '엔터테인먼트',
    other: '기타',
    
    // Filter
    keywordFilter: '키워드 필터 (쉼표로 구분)',
    resetFilters: '필터 초기화',
    noTrendData: '트렌드 데이터가 없습니다.',
    category: '카테고리',
  },
  en: {
    // Header
    title: '📊 TrendPulse',
    subtitle: 'Real-time Issue Trend Analysis',
    lastUpdate: 'Last update',
    refresh: '🔄 Refresh',
    refreshing: 'Refreshing...',
    
    // Stats
    totalCollected: 'Total Collected Data',
    totalAnalysis: 'AI Analysis Results',
    totalRankings: 'Issue Rankings',
    sourceStats: 'Source Statistics',
    
    // Issue Ranking
    issueRanking: '🏆 Issue Ranking',
    noRankingData: 'No ranking data available.',
    score: 'Score',
    mentions: 'Mentions',
    sources: 'Sources',
    issueContent: '📋 Issue Content',
    what: '📋 What',
    whyNow: '⏰ Why Now',
    context: '🌐 Context',
    
    // AI Analysis
    aiAnalysis: '🤖 AI Analysis Results',
    noAnalysisData: 'No analysis data available.',
    importance: 'Importance',
    sentiment: 'Sentiment',
    
    // Recent Data
    recentData: '📰 Recent Collected Data',
    noRecentData: 'No recent data available.',
    
    // Error
    errorLoading: 'Failed to load data. Please check if the server is running.',
    loading: 'Loading data...',
    
    // Footer
    footer: 'TrendPulse v0.1.0 | Data collection interval: 5 minutes',
    
    // Language Selection
    language: 'Language',
    korean: '한국어',
    english: 'English',
    
    // Sentiment
    positive: 'Positive',
    negative: 'Negative',
    neutral: 'Neutral',
    
    // Other
    viewOriginal: 'View Original →',
    expand: '▼ Show More',
    collapse: '▲ Collapse',
    items: 'items',
    
    // Stats
    totalTrends: 'Total Trends',
    totalInterest: 'Total Interest',
    realtimeUpdate: 'Realtime Update',
    every5Minutes: 'Every 5 minutes',
    
    // Surge Trends
    surgeTrends: '🔥 Surge Trends',
    surgeTrendsDesc: 'Trends that surged in the last 15 minutes',
    rankChange: 'Rank',
    interestIncrease: 'x increase',
    
    // Chart
    trendChart: 'Trend Chart',
    lastHour: 'Last 1 hour (5-minute intervals)',
    
    // Trend Card
    interest: 'Interest',
    changeRate: 'Change Rate',
    source: 'Source',
    
    // Categories
    all: 'All',
    news: 'News',
    social: 'Social',
    tech: 'Tech',
    entertainment: 'Entertainment',
    other: 'Other',
    
    // Filter
    keywordFilter: 'Keyword Filter (comma-separated)',
    resetFilters: 'Reset Filters',
    noTrendData: 'No trend data available.',
    category: 'Category',
  },
};

export const getTranslation = (key, language = 'ko') => {
  return translations[language]?.[key] || key;
};

