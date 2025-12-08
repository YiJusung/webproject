import React from 'react';
import { TrendingUp, TrendingDown, MessageCircle, Hash, Globe } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { getTranslation } from '../utils/translations';

function TrendCard({ trend, rank, onSelect }) {
  const { language } = useLanguage();
  const t = (key) => getTranslation(key, language);
  const isPositive = trend.change > 0;
  

  return (
    <div
      className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-200 dark:border-slate-700 hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => onSelect?.(trend, rank)}
    >
      {/* 순위 번호 - 피그마 스타일 (보라색 원) */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-full text-white font-semibold text-lg">
            {rank}
          </div>
          <div className="flex-1">
            <h3 className="text-slate-900 dark:text-white font-bold text-base leading-tight mb-1">{trend.keyword || trend.topic}</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400">{trend.category || '기타'}</p>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {/* 관심도 - 피그마 스타일 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
            <MessageCircle className="w-4 h-4" />
            <span className="text-sm font-medium">{t('interest')}</span>
          </div>
          <span className="text-slate-900 dark:text-white font-semibold">
            {(() => {
              const score = trend.interest_score || trend.mentions || trend.mention_count || 0;
              // 관심도 점수를 읽기 쉬운 형식으로 변환 (K, M 단위)
              if (score >= 1000000) {
                return (score / 1000000).toFixed(1) + 'M';
              } else if (score >= 1000) {
                return (score / 1000).toFixed(1) + 'K';
              }
              return score.toLocaleString();
            })()}
          </span>
        </div>

        {/* 변화율 - 피그마 스타일 */}
        {trend.change !== undefined && (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
              <Hash className="w-4 h-4" />
              <span className="text-sm font-medium">{t('changeRate')}</span>
            </div>
            <div className={`flex items-center gap-1 font-semibold ${isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {isPositive ? (
                <TrendingUp className="w-4 h-4" />
              ) : (
                <TrendingDown className="w-4 h-4" />
              )}
              <span>
                {isPositive ? '+' : ''}{trend.change}%
              </span>
            </div>
          </div>
        )}

        {/* 출처 정보 - 피그마 UI 스타일 */}
        {trend.sources && trend.sources.types && trend.sources.types.length > 0 && (
          <div className="pt-3 border-t border-slate-100 dark:border-slate-700">
            <div className="flex items-center gap-2 mb-2">
              <Globe className="w-3 h-3 text-slate-500 dark:text-slate-400" />
              <span className="text-xs text-slate-600 dark:text-slate-400 font-medium">{t('source')}</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {trend.sources.types.slice(0, 3).map((source, idx) => {
                const getSourceColor = (sourceType) => {
                  const colors = {
                    'news': 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800 hover:bg-blue-100 dark:hover:bg-blue-900/50',
                    'reddit': 'bg-orange-50 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 border-orange-200 dark:border-orange-800 hover:bg-orange-100 dark:hover:bg-orange-900/50',
                    'github': 'bg-slate-50 dark:bg-slate-700 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-600',
                    'youtube': 'bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800 hover:bg-red-100 dark:hover:bg-red-900/50',
                  };
                  return colors[sourceType] || 'bg-slate-50 dark:bg-slate-700 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-600';
                };
                return (
                  <button
                    key={idx}
                    onClick={(e) => {
                      e.stopPropagation(); // 카드 클릭 이벤트 방지
                    }}
                    className={`px-2.5 py-1 rounded-md text-xs font-medium border transition-colors cursor-pointer ${getSourceColor(source.type)}`}
                    title={`${source.type}: ${source.count}${t('items')}`}
                  >
                    {source.type}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* 하단: 플랫폼 - 피그마 UI 스타일 */}
        <div className="pt-3 border-t border-slate-100 dark:border-slate-700 flex items-center justify-end">
          {trend.platform && trend.platform !== 'All' && (
            <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">{trend.platform}</span>
          )}
          {(!trend.platform || trend.platform === 'All') && (
            <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">All</span>
          )}
        </div>
      </div>
    </div>
  );
}

export default TrendCard;

