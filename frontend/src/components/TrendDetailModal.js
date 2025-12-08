import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, MessageCircle, TrendingUp, BarChart3, Clock, Globe, Hash, ExternalLink, Loader2 } from 'lucide-react';
import { PieChart, Pie, Cell } from 'recharts';

// API URL 동적 감지: 현재 호스트의 IP 주소 사용
const getApiBase = () => {
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:8000/api';
  }
  return `http://${hostname}:8000/api`;
};

const API_BASE = getApiBase();

function TrendDetailModal({ trend, rank, onClose, language = 'ko' }) {
  const [detailData, setDetailData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const topic = trend.keyword || trend.topic;

  useEffect(() => {
    if (!topic) {
      setLoading(false);
      return;
    }

    const fetchDetail = async () => {
      try {
        setLoading(true);
        setError(null);
        // URL 인코딩하여 특수문자 처리
        const encodedTopic = encodeURIComponent(topic);
        const response = await axios.get(`${API_BASE}/trends/${encodedTopic}/detail?lang=${language}`);
        
        // 응답 데이터 검증
        if (response.data) {
          setDetailData(response.data);
        } else {
          setError('상세 분석 데이터가 없습니다.');
        }
      } catch (err) {
        console.error('상세 분석 데이터 로딩 실패:', err);
        const errorMessage = err.response?.data?.detail || err.message || '상세 분석 데이터를 불러올 수 없습니다.';
        setError(errorMessage);
        // 오류가 발생해도 기본 정보는 표시
        setDetailData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [topic, language]);

  const detailItems = detailData ? [
    { label: '관심도', value: (() => {
        // total_interest_score 우선 사용 (전체 관심도, 순위표와 동일)
        const score = detailData.statistics?.total_interest_score || detailData.ranking?.interest_score || detailData.ranking?.mention_count || trend.interest_score || trend.mention_count || trend.mentions || 0;
        if (score >= 1000000) return (score / 1000000).toFixed(1) + 'M';
        if (score >= 1000) return (score / 1000).toFixed(1) + 'K';
        return score.toLocaleString();
      })() },
    { label: '카테고리', value: trend.category || '기타' },
    { label: '플랫폼', value: trend.platform || 'All' },
  ] : [
    { label: '관심도', value: (() => {
        const score = trend.interest_score || trend.mention_count || trend.mentions || 0;
        if (score >= 1000000) return (score / 1000000).toFixed(1) + 'M';
        if (score >= 1000) return (score / 1000).toFixed(1) + 'K';
        return score.toLocaleString();
      })() },
    { label: '카테고리', value: trend.category || '기타' },
    { label: '플랫폼', value: trend.platform || 'All' },
    { label: '감정', value: trend.sentiment || 'neutral' },
  ];

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6 z-50">
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 text-white flex items-center justify-center text-lg font-semibold">
              {rank}
            </div>
            <div>
              <h2 className="text-xl font-semibold text-slate-900">{trend.keyword || trend.topic}</h2>
              <p className="text-sm text-slate-600">{trend.category || '기타'}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            <span className="ml-3 text-slate-600">상세 분석 데이터를 불러오는 중...</span>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {!loading && !error && detailData && (
          <>
            {/* AI 심층 분석 - DATA_FLOW.md 형식 (What, Why Now, Context) */}
            {/* API 데이터 우선 사용, 없으면 trend 데이터 사용 */}
            {(() => {
              // 사용할 데이터 결정: API 데이터 우선, 없으면 trend 데이터
              const what = detailData.analysis?.what || trend.what;
              const why_now = detailData.analysis?.why_now || trend.why_now;
              const context = detailData.analysis?.context || trend.context;
              const description = detailData.analysis?.description || trend.description;
              
              // 하나라도 있으면 표시
              if (what || why_now || context || (description && !what && !why_now && !context)) {
                return (
                  <div className="bg-gradient-to-br from-blue-50 to-purple-50 border-2 border-blue-200 rounded-xl p-6 mb-6 shadow-sm">
                    <div className="flex items-center gap-2 mb-4">
                      <TrendingUp className="w-5 h-5 text-blue-600" />
                      <h3 className="text-lg font-semibold text-slate-800">AI 심층 분석</h3>
                    </div>
                    
                    {/* What: 이슈가 무엇인지 */}
                    {what && (
                      <div className="mb-4 pb-4 border-b border-blue-200">
                        <div className="flex items-center gap-2 mb-2">
                          <div className="w-2 h-2 rounded-full bg-blue-600"></div>
                          <p className="text-sm font-semibold text-blue-900">What: 이슈가 무엇인가?</p>
                        </div>
                        <p className="text-sm text-slate-800 leading-relaxed pl-4">{what}</p>
                      </div>
                    )}
                    
                    {/* Why Now: 왜 지금 이슈가 되고 있는지 */}
                    {why_now && (
                      <div className="mb-4 pb-4 border-b border-blue-200">
                        <div className="flex items-center gap-2 mb-2">
                          <div className="w-2 h-2 rounded-full bg-purple-600"></div>
                          <p className="text-sm font-semibold text-purple-900">Why Now: 왜 지금 이슈가 되고 있는가?</p>
                        </div>
                        <p className="text-sm text-slate-800 leading-relaxed pl-4">{why_now}</p>
                      </div>
                    )}
                    
                    {/* Context: 배경 맥락 */}
                    {context && (
                      <div className="mb-4">
                        <div className="flex items-center gap-2 mb-2">
                          <div className="w-2 h-2 rounded-full bg-indigo-600"></div>
                          <p className="text-sm font-semibold text-indigo-900">Context: 배경 맥락</p>
                        </div>
                        <p className="text-sm text-slate-800 leading-relaxed pl-4">{context}</p>
                      </div>
                    )}
                    
                    {/* Description: 요약 (what, why_now, context가 모두 없을 때만) */}
                    {description && !what && !why_now && !context && (
                      <div className="mt-4 pt-4 border-t border-blue-200">
                        <p className="text-xs text-slate-600 mb-1">요약</p>
                        <p className="text-sm text-slate-700">{description}</p>
                      </div>
                    )}
                  </div>
                );
              }
              return null;
            })()}

            {/* Source Distribution */}
            {detailData.statistics?.source_distribution && Object.keys(detailData.statistics.source_distribution).length > 0 && (
              <div className="bg-white border border-slate-200 rounded-xl p-4 mb-6">
                <h3 className="text-slate-800 font-medium mb-4 flex items-center gap-2">
                  <Globe className="w-5 h-5" />
                  출처별 분포
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {Object.entries(detailData.statistics.source_distribution).map(([source, count]) => {
                    const getSourceColor = (sourceType) => {
                      const colors = {
                        'news': 'bg-blue-50 text-blue-700 border-blue-200',
                        'reddit': 'bg-orange-50 text-orange-700 border-orange-200',
                        'github': 'bg-slate-50 text-slate-700 border-slate-200',
                        'youtube': 'bg-red-50 text-red-700 border-red-200',
                      };
                      return colors[sourceType] || 'bg-slate-50 text-slate-700 border-slate-200';
                    };
                    return (
                      <div key={source} className={`border rounded-lg p-3 ${getSourceColor(source)}`}>
                        <p className="text-xs font-medium mb-1">{source.toUpperCase()}</p>
                        <p className="text-slate-900 font-semibold">{count}개</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* 주요 출처 (랭킹 API에서 제공) */}
            {trend.sources && (trend.sources.types?.length > 0 || trend.sources.names?.length > 0) && (
              <div className="bg-white border border-slate-200 rounded-xl p-4 mb-6">
                <h3 className="text-slate-800 font-medium mb-4 flex items-center gap-2">
                  <Globe className="w-5 h-5" />
                  주요 출처
                </h3>
                {trend.sources.types?.length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs text-slate-600 mb-2">소스 타입</p>
                    <div className="flex flex-wrap gap-2">
                      {trend.sources.types.map((source, idx) => {
                        const getSourceColor = (sourceType) => {
                          const colors = {
                            'news': 'bg-blue-100 text-blue-700 border-blue-300',
                            'reddit': 'bg-orange-100 text-orange-700 border-orange-300',
                            'github': 'bg-slate-100 text-slate-700 border-slate-300',
                            'youtube': 'bg-red-100 text-red-700 border-red-300',
                          };
                          return colors[sourceType] || 'bg-slate-100 text-slate-700 border-slate-300';
                        };
                        return (
                          <span 
                            key={idx}
                            className={`px-3 py-1.5 rounded-lg text-sm font-medium border ${getSourceColor(source.type)}`}
                          >
                            {source.type} ({source.count})
                          </span>
                        );
                      })}
                    </div>
                  </div>
                )}
                {trend.sources.names?.length > 0 && (
                  <div>
                    <p className="text-xs text-slate-600 mb-2">주요 소스</p>
                    <div className="flex flex-wrap gap-2">
                      {trend.sources.names.map((source, idx) => (
                        <span 
                          key={idx}
                          className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded-lg text-sm border border-slate-300"
                        >
                          {source.name} ({source.count})
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Sentiment Distribution */}
            {detailData.statistics?.sentiment_distribution && Object.keys(detailData.statistics.sentiment_distribution).length > 0 && (
              <div className="bg-white border border-slate-200 rounded-xl p-4 mb-6">
                <h3 className="text-slate-800 font-medium mb-4">감정 분석 분포</h3>
                <div className="flex gap-4">
                  {Object.entries(detailData.statistics.sentiment_distribution).map(([sentiment, count]) => {
                    const colors = {
                      positive: 'bg-green-100 text-green-700 border-green-200',
                      negative: 'bg-red-100 text-red-700 border-red-200',
                      neutral: 'bg-slate-100 text-slate-700 border-slate-200'
                    };
                    return (
                      <div key={sentiment} className={`border rounded-lg px-4 py-2 ${colors[sentiment] || colors.neutral}`}>
                        <p className="text-xs">{sentiment === 'positive' ? '긍정' : sentiment === 'negative' ? '부정' : '중립'}</p>
                        <p className="font-medium">{count}회</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Keywords */}
            {detailData.keywords && detailData.keywords.length > 0 && (
              <div className="bg-white border border-slate-200 rounded-xl p-4 mb-6">
                <h3 className="text-slate-800 font-medium mb-4 flex items-center gap-2">
                  <Hash className="w-5 h-5" />
                  관련 키워드
                </h3>
                <div className="flex flex-wrap gap-2">
                  {detailData.keywords.map((kw, idx) => (
                    <span key={idx} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm border border-blue-100">
                      {kw.keyword} ({kw.count})
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Related Items */}
            {detailData.related_items && detailData.related_items.length > 0 && (
              <div className="bg-white border border-slate-200 rounded-xl p-4 mb-6">
                <h3 className="text-slate-800 font-medium mb-4">관련 아이템 ({detailData.related_items.length}개)</h3>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {detailData.related_items.map((item) => (
                    <div key={item.id} className="border border-slate-200 rounded-lg p-3 hover:bg-slate-50 transition-colors">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-slate-900 mb-1">{item.title}</p>
                          {item.content && (
                            <p className="text-xs text-slate-600 mb-2 line-clamp-2">{item.content}</p>
                          )}
                          <div className="flex items-center gap-2 text-xs text-slate-500">
                            <span>{item.source}</span>
                            <span>•</span>
                            <span>{item.source_type}</span>
                            {item.collected_at && (
                              <>
                                <span>•</span>
                                <span>{new Date(item.collected_at).toLocaleString()}</span>
                              </>
                            )}
                          </div>
                        </div>
                        {item.url && (
                          <a 
                            href={item.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="p-2 text-slate-500 hover:text-blue-600 transition-colors"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* Fallback to basic info if API fails - DATA_FLOW.md 형식 */}
        {/* detailData가 없거나 error가 있을 때만 표시 (위에서 이미 표시했으면 여기서는 표시 안 함) */}
        {!loading && (!detailData || error) && (trend.what || trend.why_now || trend.context) && (
          <div className="bg-gradient-to-br from-blue-50 to-purple-50 border-2 border-blue-200 rounded-xl p-6 mb-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-5 h-5 text-blue-600" />
              <h3 className="text-lg font-semibold text-slate-800">AI 심층 분석</h3>
            </div>
            
            {/* What: 이슈가 무엇인지 */}
            {trend.what && (
              <div className="mb-4 pb-4 border-b border-blue-200">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 rounded-full bg-blue-600"></div>
                  <p className="text-sm font-semibold text-blue-900">What: 이슈가 무엇인가?</p>
                </div>
                <p className="text-sm text-slate-800 leading-relaxed pl-4">{trend.what}</p>
              </div>
            )}
            
            {/* Why Now: 왜 지금 이슈가 되고 있는지 */}
            {trend.why_now && (
              <div className="mb-4 pb-4 border-b border-blue-200">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 rounded-full bg-purple-600"></div>
                  <p className="text-sm font-semibold text-purple-900">Why Now: 왜 지금 이슈가 되고 있는가?</p>
                </div>
                <p className="text-sm text-slate-800 leading-relaxed pl-4">{trend.why_now}</p>
              </div>
            )}
            
            {/* Context: 배경 맥락 */}
            {trend.context && (
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 rounded-full bg-indigo-600"></div>
                  <p className="text-sm font-semibold text-indigo-900">Context: 배경 맥락</p>
                </div>
                <p className="text-sm text-slate-800 leading-relaxed pl-4">{trend.context}</p>
              </div>
            )}
            
            {/* Description: 요약 (선택적) */}
            {trend.description && !trend.what && !trend.why_now && !trend.context && (
              <div className="mt-4 pt-4 border-t border-blue-200">
                <p className="text-xs text-slate-600 mb-1">요약</p>
                <p className="text-sm text-slate-700">{trend.description}</p>
              </div>
            )}
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
          {detailItems.map((item) => (
            <div key={item.label} className="border border-slate-200 rounded-lg p-3">
              <p className="text-xs text-slate-500">{item.label}</p>
              <p className="text-slate-900 font-medium">{item.value}</p>
            </div>
          ))}
        </div>

        {/* Meta info */}
        <div className="flex flex-wrap gap-3 text-sm text-slate-600">
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-100">
            <MessageCircle className="w-4 h-4" /> 관심도 심층 분석
          </span>
          {trend.period_start && (
            <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-slate-50 text-slate-700 border border-slate-200">
              <Clock className="w-4 h-4" /> 시작: {trend.period_start}
            </span>
          )}
          {trend.period_end && (
            <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-slate-50 text-slate-700 border border-slate-200">
              <Clock className="w-4 h-4" /> 종료: {trend.period_end}
            </span>
          )}
          {trend.platform && (
            <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-purple-50 text-purple-700 border border-purple-100">
              <Globe className="w-4 h-4" /> {trend.platform}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default TrendDetailModal;

