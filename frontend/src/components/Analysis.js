import React from 'react';
import './Analysis.css';
import { useLanguage } from '../contexts/LanguageContext';
import { getTranslation } from '../utils/translations';

function Analysis({ analysis }) {
  const { language } = useLanguage();
  const t = (key) => getTranslation(key, language);
  const getSentimentColor = (sentiment) => {
    const colors = {
      positive: '#4caf50',
      negative: '#f44336',
      neutral: '#9e9e9e'
    };
    return colors[sentiment] || colors.neutral;
  };

  const getSentimentEmoji = (sentiment) => {
    const emojis = {
      positive: '😊',
      negative: '😟',
      neutral: '😐'
    };
    return emojis[sentiment] || emojis.neutral;
  };

  const getSentimentText = (sentiment) => {
    return t(sentiment) || sentiment;
  };

  return (
    <div className="card">
      <h2>{t('aiAnalysis')}</h2>
      <div className="analysis-list">
        {analysis.map((item, index) => (
          <div key={item.id || index} className="analysis-item">
            <div className="analysis-header">
              <h3>{item.topic}</h3>
              <div className="analysis-badges">
                <span 
                  className="sentiment-badge"
                  style={{ backgroundColor: getSentimentColor(item.sentiment) }}
                >
                  {getSentimentEmoji(item.sentiment)} {getSentimentText(item.sentiment)}
                </span>
                <span className="score-badge">
                  {t('importance')}: {item.importance_score?.toFixed(2) || 'N/A'}
                </span>
              </div>
            </div>
            
            {item.what && (
              <div className="analysis-section">
                <div className="section-label">{t('what')}:</div>
                <div className="section-content">{item.what}</div>
              </div>
            )}
            
            {item.why_now && (
              <div className="analysis-section highlight">
                <div className="section-label">{t('whyNow')}:</div>
                <div className="section-content">{item.why_now}</div>
              </div>
            )}
            
            {item.context && (
              <div className="analysis-section">
                <div className="section-label">{t('context')}:</div>
                <div className="section-content">{item.context}</div>
              </div>
            )}
            
            {!item.what && !item.why_now && !item.context && item.summary && (
              <div className="analysis-summary">
                {item.summary}
              </div>
            )}
            
            {item.keywords && item.keywords.length > 0 && (
              <div className="analysis-keywords">
                {item.keywords.map((keyword, idx) => (
                  <span key={idx} className="keyword-tag">
                    {keyword}
                  </span>
                ))}
              </div>
            )}
            
            <div className="analysis-footer">
              <span className="source-count">
                📰 {item.source_count || 0}{language === 'ko' ? '개 소스' : ' sources'}
              </span>
              {item.analyzed_at && (
                <span className="analysis-time">
                  {new Date(item.analyzed_at).toLocaleString(language === 'ko' ? 'ko-KR' : 'en-US')}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Analysis;


