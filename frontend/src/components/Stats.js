import React from 'react';
import './Stats.css';
import { useLanguage } from '../contexts/LanguageContext';
import { getTranslation } from '../utils/translations';

function Stats({ stats }) {
  const { language } = useLanguage();
  const t = (key) => getTranslation(key, language);
  const sourceCounts = stats.source_counts || {};
  const total = stats.total_collected || 0;

  return (
    <div className="stats-container">
      <div className="stat-card">
        <div className="stat-icon">📊</div>
        <div className="stat-info">
          <div className="stat-value">{total.toLocaleString()}</div>
          <div className="stat-label">{t('totalCollected')}</div>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-icon">🤖</div>
        <div className="stat-info">
          <div className="stat-value">{stats.total_analysis || 0}</div>
          <div className="stat-label">{t('totalAnalysis')}</div>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-icon">🏆</div>
        <div className="stat-info">
          <div className="stat-value">{stats.total_rankings || 0}</div>
          <div className="stat-label">{t('totalRankings')}</div>
        </div>
      </div>

      <div className="stat-card sources">
        <div className="stat-icon">📰</div>
        <div className="stat-info">
          <div className="stat-label">{t('sourceStats')}</div>
          <div className="source-list">
            {Object.entries(sourceCounts).map(([source, count]) => (
              <div key={source} className="source-item">
                <span className="source-name">{source}</span>
                <span className="source-count">{count}{language === 'ko' ? '개' : ''}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Stats;


