import React from 'react';
import './Rankings.css';
import { useLanguage } from '../contexts/LanguageContext';
import { getTranslation } from '../utils/translations';

function Rankings({ rankings }) {
  const { language } = useLanguage();
  const t = (key) => getTranslation(key, language);
  const getRankEmoji = (rank) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `${rank}.`;
  };

  const getScoreColor = (score) => {
    if (score >= 0.7) return '#4caf50';
    if (score >= 0.4) return '#ff9800';
    return '#f44336';
  };

  return (
    <div className="card">
      <h2>{t('issueRanking')}</h2>
      <div className="rankings-list">
        {rankings.map((ranking) => (
          <div key={ranking.rank} className="ranking-item">
            <div className="ranking-header">
              <div className="ranking-number">
                {getRankEmoji(ranking.rank)}
              </div>
              <div className="ranking-topic">
                <h3>{ranking.topic}</h3>
                <div className="ranking-meta">
                  <span className="meta-item">
                    📊 {t('score')}: <strong style={{ color: getScoreColor(ranking.score) }}>
                      {ranking.score.toFixed(3)}
                    </strong>
                  </span>
                  <span className="meta-item">
                    💬 {t('mentions')}: {ranking.mention_count}{language === 'ko' ? '회' : ''}
                  </span>
                  <span className="meta-item">
                    📰 {t('sources')}: {ranking.source_diversity}{language === 'ko' ? '개' : ''}
                  </span>
                </div>
              </div>
            </div>
            
            {/* 이슈 설명 표시 (내용 기반) */}
            {ranking.description && (
              <div className="ranking-description">
                <div className="description-label">{t('issueContent')}:</div>
                <div className="description-content">{ranking.description}</div>
              </div>
            )}
            
            {ranking.why_now && (
              <div className="ranking-section highlight">
                <div className="section-label">{t('whyNow')}:</div>
                <div className="section-content">{ranking.why_now}</div>
              </div>
            )}
            
            {ranking.what && !ranking.why_now && (
              <div className="ranking-section">
                <div className="section-label">{t('what')}:</div>
                <div className="section-content">{ranking.what}</div>
              </div>
            )}
            
            {ranking.context && (
              <div className="ranking-section">
                <div className="section-label">{t('context')}:</div>
                <div className="section-content">{ranking.context}</div>
              </div>
            )}
            
            <div className="score-bar-container">
              <div 
                className="score-bar" 
                style={{ 
                  width: `${ranking.score * 100}%`,
                  backgroundColor: getScoreColor(ranking.score)
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Rankings;


