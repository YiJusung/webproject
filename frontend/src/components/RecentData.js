import React, { useState } from 'react';
import './RecentData.css';
import { useLanguage } from '../contexts/LanguageContext';
import { getTranslation } from '../utils/translations';

function RecentData({ data }) {
  const { language } = useLanguage();
  const t = (key) => getTranslation(key, language);
  const [expanded, setExpanded] = useState(false);
  const displayData = expanded ? data : data.slice(0, 5);

  const getSourceIcon = (sourceType) => {
    const icons = {
      news: '📰',
      reddit: '🔴',
      github: '💻',
      youtube: '📺'
    };
    return icons[sourceType] || '📄';
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString(language === 'ko' ? 'ko-KR' : 'en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="card">
      <h2>{t('recentData')}</h2>
      <div className="recent-list">
        {displayData.map((item, index) => (
          <div key={item.id || index} className="recent-item">
            <div className="recent-header">
              <span className="source-icon">{getSourceIcon(item.source_type)}</span>
              <div className="recent-info">
                <div className="recent-source">{item.source}</div>
                <div className="recent-time">{formatDate(item.collected_at)}</div>
              </div>
            </div>
            <div className="recent-title">{item.title}</div>
            {item.url && (
              <a 
                href={item.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="recent-link"
              >
                {t('viewOriginal')}
              </a>
            )}
          </div>
        ))}
      </div>
      {data.length > 5 && (
        <button 
          className="expand-btn"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? t('collapse') : `${t('expand')} (${data.length - 5}${language === 'ko' ? '개' : ' ' + t('items')})`}
        </button>
      )}
    </div>
  );
}

export default RecentData;


