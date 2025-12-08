import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { TrendingUp, Clock, Globe, Flame, Moon, Sun } from 'lucide-react';
import TrendCard from './components/TrendCard';
import TrendChart from './components/TrendChart';
import CategoryFilter from './components/CategoryFilter';
import TrendDetailModal from './components/TrendDetailModal';
import { LanguageProvider, useLanguage } from './contexts/LanguageContext';
import { DarkModeProvider, useDarkMode } from './contexts/DarkModeContext';
import { getTranslation } from './utils/translations';
import './App.css';

// API URL 동적 감지: 현재 호스트의 IP 주소 또는 ngrok URL 사용
const getApiBase = () => {
  // 환경 변수가 설정되어 있으면 우선 사용
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // 개발 환경에서 동적으로 감지
  const hostname = window.location.hostname;
  const protocol = window.location.protocol; // http: 또는 https:
  
  // localhost나 127.0.0.1이면 localhost 사용
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:8000/api';
  }
  
  // ngrok 도메인인 경우 (ngrok.io, ngrok-free.app 등)
  if (hostname.includes('ngrok.io') || hostname.includes('ngrok-free.app') || hostname.includes('ngrok.app')) {
    // ngrok은 HTTPS를 사용하므로 같은 호스트의 8000 포트 사용
    // 백엔드도 별도의 ngrok 터널이 필요함
    // 환경 변수로 설정하거나, 프론트엔드와 같은 포트를 사용하도록 설정 필요
    return `${protocol}//${hostname.replace(':3000', ':8000')}/api`;
  }
  
  // 다른 IP 주소로 접속한 경우 같은 호스트의 8000 포트 사용
  return `http://${hostname}:8000/api`;
};

const API_BASE = getApiBase();

function AppContent() {
  const { language, toggleLanguage } = useLanguage();
  const { darkMode, toggleDarkMode } = useDarkMode();
  // memoize translator to avoid recreating on every render (eslint exhaustive-deps)
  const t = useCallback((key) => getTranslation(key, language), [language]);
  
  const [stats, setStats] = useState(null);
  const [rankings, setRankings] = useState([]);
  const [surgeTrends, setSurgeTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [selectedCategory, setSelectedCategory] = useState(() => {
    // 언어에 따라 초기값 설정
    const saved = localStorage.getItem('hourly-pulse-language');
    return saved === 'en' ? 'All' : '전체';
  });
  const [keywordFilter, setKeywordFilter] = useState('');
  const [selectedTrend, setSelectedTrend] = useState(null);
  const [selectedRank, setSelectedRank] = useState(null);

  const fetchData = React.useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [statsRes, rankingsRes, surgeRes] = await Promise.all([
        axios.get(`${API_BASE}/stats`).catch(() => ({ data: null })),
        axios.get(`${API_BASE}/rankings?limit=10&lang=${language}`).catch(() => ({ data: [] })),
        axios.get(`${API_BASE}/surge-trends?limit=5&lang=${language}`).catch(() => ({ data: [] })),
      ]);

      setStats(statsRes.data);
      setRankings(rankingsRes.data || []);
      setSurgeTrends(surgeRes.data || []);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('데이터 로딩 실패:', err);
      setError(t('errorLoading'));
    } finally {
      setLoading(false);
    }
  }, [language, t]);

  useEffect(() => {
    fetchData();
    // 5초마다 자동 새로고침 (피그마 디자인에 맞춤)
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // 언어 변경 시 카테고리 초기값 업데이트
  useEffect(() => {
    const allCategories = {
      'ko': '전체',
      'en': 'All'
    };
    const currentAll = allCategories[language];
    
    // 현재 선택된 카테고리가 '전체' 또는 'All'이면 언어에 맞게 변경
    if (selectedCategory === '전체' || selectedCategory === 'All') {
      setSelectedCategory(currentAll);
    }
  }, [language]);

  // 트렌드 데이터 변환 (rankings를 피그마 디자인 형식으로)
  const convertToTrends = useCallback(() => {
    // rankings가 배열이 아닌 경우 빈 배열 반환
    if (!Array.isArray(rankings)) {
      return [];
    }
    return rankings.map((ranking, index) => {
      // 카테고리 결정: 소스 타입 기반 또는 기본값
      const sourceTypes = ranking.sources?.types || [];
      let category = t('other');
      if (sourceTypes.length > 0) {
        const primarySource = sourceTypes[0].type;
        const categoryMap = {
          'news': t('news'),
          'reddit': t('social'),
          'github': t('tech'),
          'youtube': t('entertainment')
        };
        category = categoryMap[primarySource] || t('other');
      }

      // 변화율 계산: trend_direction 기반 또는 기본값
      let change = 0;
      if (ranking.trend_direction === 'up') {
        change = Math.floor(Math.random() * 100) + 10; // 10-110% 상승
      } else if (ranking.trend_direction === 'down') {
        change = -(Math.floor(Math.random() * 50) + 1); // -1 ~ -50% 하락
      } else {
        change = Math.floor(Math.random() * 20) - 10; // -10 ~ +10% 안정
      }

      // 감정 정보: API에서 가져오거나 기본값
      const sentiment = ranking.sentiment || 'neutral';

      // 플랫폼: 소스 타입들을 조합
      const platform = sourceTypes.length > 0 
        ? sourceTypes.map(s => s.type).join(', ')
        : 'All';

      return {
        id: index + 1,
        keyword: ranking.topic || ranking.title || 'Unknown',
        topic: ranking.topic, // 상세 모달에서 사용
        category: category,
        mentions: ranking.interest_score || ranking.mention_count || ranking.mentions || 0,
        mention_count: ranking.interest_score || ranking.mention_count, // 관심도 점수 사용
        interest_score: ranking.interest_score || ranking.mention_count, // 관심도 점수
        change: change,
        sentiment: sentiment,
        platform: platform,
        timestamp: ranking.timestamp || new Date().toISOString(),
        // 상세 분석에 필요한 추가 데이터 (AI 가공 정보)
        description: ranking.description,
        what: ranking.what,
        why_now: ranking.why_now,
        context: ranking.context,
        score: ranking.score,
        source_diversity: ranking.source_diversity,
        trend_direction: ranking.trend_direction,
        period_start: ranking.period_start,
        period_end: ranking.period_end,
        // 출처 정보 (피그마 UI에 표시)
        sources: ranking.sources || { types: [], names: [] },
      };
    });
  }, [rankings, t]);

  const trends = convertToTrends();
  const categories = [t('all'), ...Array.from(new Set(trends.map(trend => trend.category)))];
  
  const filteredTrends = trends.filter((trend) => {
    // 카테고리 필터
    if (selectedCategory !== t('all') && trend.category !== selectedCategory) return false;
    
    const keywordText = `${t.keyword || t.topic || ''} ${t.category || ''}`.toLowerCase();

    const filters = keywordFilter
      .split(',')
      .map((k) => k.trim().toLowerCase())
      .filter(Boolean);
    const matchesKeywordFilter = filters.length
      ? filters.some((f) => keywordText.includes(f))
      : true;

    return matchesKeywordFilter;
  });

  const sortedTrends = [...filteredTrends].sort((a, b) => b.mentions - a.mentions);
  const totalMentions = trends.reduce((acc, trend) => acc + trend.mentions, 0);

  if (loading && !stats) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center">
        <div className="text-center">
          <div className="spinner border-4 border-blue-500 dark:border-blue-400 border-t-transparent rounded-full w-12 h-12 mx-auto mb-4 animate-spin"></div>
          <p className="text-slate-600 dark:text-slate-400">{t('loading')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
                <TrendingUp className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-medium text-slate-900 dark:text-white">{t('title')}</h1>
                <p className="text-slate-600 dark:text-slate-400 text-sm">{t('subtitle')}</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                <Clock className="w-4 h-4" />
                <span className="text-sm">
                  {t('lastUpdate')}: {lastUpdate.toLocaleTimeString(language === 'ko' ? 'ko-KR' : 'en-US')}
                </span>
              </div>
              <button 
                onClick={toggleDarkMode} 
                className="px-3 py-1 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors text-sm"
                title={darkMode ? '라이트 모드' : '다크 모드'}
              >
                {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>
              <button 
                onClick={toggleLanguage} 
                className="px-3 py-1 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors text-sm"
                title={t('language')}
              >
                {language === 'ko' ? '🇰🇷' : '🇺🇸'}
              </button>
              <button 
                onClick={fetchData} 
                className="px-4 py-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors text-sm"
                disabled={loading}
              >
                {loading ? t('refreshing') : t('refresh')}
              </button>
            </div>
          </div>
          
          {/* 키워드 필터 */}
          {keywordFilter && (
            <div className="mt-4 flex items-center gap-3">
              <input
                type="text"
                placeholder={t('keywordFilter')}
                value={keywordFilter}
                onChange={(e) => setKeywordFilter(e.target.value)}
                className="flex-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-700 text-slate-900 dark:text-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={() => {
                  setKeywordFilter('');
                  setSelectedCategory(t('all'));
                }}
                className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 text-sm"
              >
                {t('resetFilters')}
              </button>
            </div>
          )}
        </div>
      </header>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 dark:border-red-400 text-red-700 dark:text-red-300 p-4 mx-4 mt-4 rounded">
          <p className="font-medium">⚠️ {error}</p>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-200 dark:border-slate-700">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <Globe className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-slate-600 dark:text-slate-400 text-sm">{t('totalTrends')}</p>
                <p className="text-slate-900 dark:text-white text-xl font-medium">{trends.length}개</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-200 dark:border-slate-700">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <TrendingUp className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-slate-600 dark:text-slate-400 text-sm">{t('totalInterest')}</p>
                <p className="text-slate-900 dark:text-white text-xl font-medium">
                  {totalMentions >= 1000000
                    ? `${(totalMentions / 1000000).toFixed(1)}M`
                    : totalMentions >= 1000 
                    ? `${(totalMentions / 1000).toFixed(1)}K`
                    : totalMentions.toLocaleString()}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  {totalMentions.toLocaleString()}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-200 dark:border-slate-700">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <Clock className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-slate-600 dark:text-slate-400 text-sm">{t('realtimeUpdate')}</p>
                <p className="text-slate-900 dark:text-white text-xl font-medium">{t('every5Minutes')}</p>
              </div>
            </div>
          </div>
        </div>

        {/* 급상승 트렌드 섹션 */}
        {surgeTrends.length > 0 && (
          <div className="bg-gradient-to-r from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20 rounded-xl p-6 shadow-sm border-2 border-orange-200 dark:border-orange-800 mb-8">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-orange-500 dark:bg-orange-600 rounded-lg">
                <Flame className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{t('surgeTrends')}</h2>
                <p className="text-sm text-slate-600 dark:text-slate-400">{t('surgeTrendsDesc')}</p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {surgeTrends.map((surge, index) => {
                const categoryMap = {
                  'news': t('news'),
                  'reddit': t('social'),
                  'github': t('tech'),
                  'youtube': t('entertainment')
                };
                const sourceTypes = surge.sources?.types || [];
                const category = sourceTypes.length > 0 
                  ? categoryMap[sourceTypes[0].type] || t('other')
                  : t('other');
                
                return (
                  <div
                    key={index}
                    onClick={() => {
                      const trend = {
                        id: index + 1,
                        keyword: surge.topic,
                        topic: surge.topic,
                        category: category,
                        mentions: surge.current_interest,
                        mention_count: surge.current_interest,
                        interest_score: surge.current_interest,
                        change: surge.interest_change_rate,
                        sentiment: 'positive',
                        platform: sourceTypes.map(s => s.type).join(', ') || 'All',
                        timestamp: new Date().toISOString(),
                        description: surge.description,
                        what: surge.what,
                        why_now: surge.why_now,
                        context: surge.context,
                        sources: surge.sources || { types: [], names: [] },
                      };
                      setSelectedTrend(trend);
                      setSelectedRank(surge.current_rank);
                    }}
                    className="bg-white dark:bg-slate-800 rounded-lg p-4 border-2 border-orange-300 dark:border-orange-700 hover:border-orange-400 dark:hover:border-orange-600 cursor-pointer transition-all hover:shadow-lg"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h3 className="font-semibold text-slate-900 dark:text-white mb-1 line-clamp-2">
                          {surge.topic}
                        </h3>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">{category}</p>
                      </div>
                      <div className="flex items-center gap-1 text-orange-600">
                        <TrendingUp className="w-4 h-4" />
                        <span className="text-sm font-bold">
                          +{surge.interest_change_rate.toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-400">
                      <span>{t('rankChange')}: {surge.previous_rank} → {surge.current_rank}</span>
                      <span className="text-orange-600 dark:text-orange-400 font-medium">
                        {surge.interest_multiplier.toFixed(1)}{t('interestIncrease')}
                      </span>
                    </div>
                    {surge.surge_reason && (
                      <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-700">
                        <p className="text-xs text-slate-600 dark:text-slate-400">{surge.surge_reason}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Chart Section */}
        {sortedTrends.length > 0 && (
          <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-200 dark:border-slate-700 mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-slate-900 dark:text-white font-medium">{t('trendChart')}</h2>
              <span className="text-xs text-slate-500 dark:text-slate-400">{t('lastHour')}</span>
            </div>
            <TrendChart trends={sortedTrends.slice(0, 5)} />
          </div>
        )}

        {/* Category Filter */}
        {categories.length > 1 && (
          <CategoryFilter 
            categories={categories}
            selectedCategory={selectedCategory}
            onSelectCategory={setSelectedCategory}
          />
        )}

        {/* Trends Grid */}
        {sortedTrends.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sortedTrends.map((trend, index) => (
              <TrendCard 
                key={trend.id} 
                trend={trend} 
                rank={index + 1}
                onSelect={(t) => {
                  setSelectedTrend(t);
                  setSelectedRank(index + 1);
                }}
              />
            ))}
          </div>
        ) : (
                <div className="bg-white dark:bg-slate-800 rounded-xl p-12 shadow-sm border border-slate-200 dark:border-slate-700 text-center">
                  <p className="text-slate-600 dark:text-slate-400">{t('noTrendData')}</p>
                </div>
        )}
      </div>

      {/* Trend Detail Modal */}
      {selectedTrend && (
        <TrendDetailModal
          trend={selectedTrend}
          rank={selectedRank}
          language={language}
          onClose={() => {
            setSelectedTrend(null);
            setSelectedRank(null);
          }}
        />
      )}
    </div>
  );
}

function App() {
  return (
    <DarkModeProvider>
      <LanguageProvider>
        <AppContent />
      </LanguageProvider>
    </DarkModeProvider>
  );
}

export default App;
