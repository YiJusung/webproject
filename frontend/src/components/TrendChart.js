import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TrendingUp } from 'lucide-react';

function TrendChart({ trends }) {
  // 상위 5개 트렌드 선택
  const topTrends = trends.slice(0, 5);
  
  // 색상 팔레트 개선
  const colors = [
    { stroke: '#3b82f6', fill: '#3b82f6', gradient: ['#3b82f6', '#60a5fa'] }, // Blue
    { stroke: '#8b5cf6', fill: '#8b5cf6', gradient: ['#8b5cf6', '#a78bfa'] }, // Purple
    { stroke: '#ec4899', fill: '#ec4899', gradient: ['#ec4899', '#f472b6'] }, // Pink
    { stroke: '#10b981', fill: '#10b981', gradient: ['#10b981', '#34d399'] }, // Green
    { stroke: '#f59e0b', fill: '#f59e0b', gradient: ['#f59e0b', '#fbbf24'] }, // Amber
  ];

  // 관심도 포맷팅 함수
  const formatInterest = (value) => {
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
    return value.toLocaleString();
  };

  // 차트 데이터 생성 (5분 간격, 최근 1시간)
  const generateChartData = () => {
    // 현재 시간을 5분 단위로 내림 (예: 21:47 -> 21:45)
    const now = new Date();
    const currentMinute = now.getMinutes();
    const flooredMinute = Math.floor(currentMinute / 5) * 5;
    const baseTime = new Date(now);
    baseTime.setMinutes(flooredMinute, 0, 0);
    
    // 최근 1시간을 5분 간격으로 12개 구간 생성
    const timePoints = [];
    for (let i = 11; i >= 0; i--) {
      const time = new Date(baseTime);
      time.setMinutes(time.getMinutes() - (i * 5));
      const timeStr = `${time.getHours().toString().padStart(2, '0')}:${time.getMinutes().toString().padStart(2, '0')}`;
      timePoints.push({ time: timeStr, timestamp: time.getTime() });
    }
    
    // 각 트렌드의 관심도가 시간에 따라 변동하는 것을 시뮬레이션
    // 최근 구간일수록 현재 관심도에 가깝고, 과거 구간일수록 낮은 값
    return timePoints.map((timePoint, index) => {
      const dataPoint = { time: timePoint.time };
      const progress = index / 11; // 0 (과거) ~ 1 (현재)
      
      topTrends.forEach((trend) => {
        const keyword = trend.keyword || trend.topic || 'Unknown';
        const currentScore = trend.interest_score || trend.mentions || trend.mention_count || 0;
        
        // 과거 구간일수록 낮은 값, 현재 구간에 가까울수록 현재 값에 가까움
        // 선형 보간: 과거(0%) = 현재의 60%, 현재(100%) = 현재의 100%
        const scoreMultiplier = 0.6 + (progress * 0.4);
        // 약간의 자연스러운 변동 추가 (sin 파형)
        const naturalVariation = 1 + (Math.sin(index * 0.8) * 0.1);
        const calculatedScore = Math.floor(currentScore * scoreMultiplier * naturalVariation);
        
        dataPoint[keyword] = calculatedScore;
      });
      return dataPoint;
    });
  };

  const chartData = generateChartData();

  if (!trends || trends.length === 0) {
    return (
      <div className="h-[350px] flex flex-col items-center justify-center text-slate-500 bg-slate-50 rounded-lg">
        <TrendingUp className="w-12 h-12 mb-3 text-slate-400" />
        <p className="text-sm">차트 데이터가 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={350}>
        <AreaChart 
          data={chartData}
          margin={{ top: 10, right: 20, left: 0, bottom: 50 }}
        >
          <defs>
            {topTrends.map((trend, index) => {
              const keyword = trend.keyword || trend.topic || 'Unknown';
              const color = colors[index % colors.length];
              return (
                <linearGradient key={keyword} id={`gradient${index}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={color.gradient[0]} stopOpacity={0.4}/>
                  <stop offset="50%" stopColor={color.gradient[1]} stopOpacity={0.2}/>
                  <stop offset="95%" stopColor={color.gradient[0]} stopOpacity={0}/>
                </linearGradient>
              );
            })}
          </defs>
          <CartesianGrid 
            strokeDasharray="3 3" 
            stroke="#e2e8f0" 
            vertical={false}
            opacity={0.5}
          />
          <XAxis 
            dataKey="time" 
            stroke="#64748b"
            style={{ fontSize: '11px', fontWeight: 500 }}
            tick={{ fill: '#64748b' }}
            axisLine={{ stroke: '#cbd5e1' }}
            tickLine={{ stroke: '#cbd5e1' }}
            interval={1} // 모든 시간대 표시
            angle={-45} // 시간 레이블을 45도 회전
            textAnchor="end"
            height={60} // 회전된 레이블을 위한 공간 확보
          />
          <YAxis 
            stroke="#64748b"
            style={{ fontSize: '11px', fontWeight: 500 }}
            tick={{ fill: '#64748b' }}
            axisLine={{ stroke: '#cbd5e1' }}
            tickLine={{ stroke: '#cbd5e1' }}
            tickFormatter={formatInterest}
            width={60}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'white',
              border: '1px solid #e2e8f0',
              borderRadius: '12px',
              boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -2px rgb(0 0 0 / 0.05)',
              padding: '12px',
              fontSize: '13px'
            }}
            labelStyle={{ 
              fontWeight: 600,
              color: '#1e293b',
              marginBottom: '8px'
            }}
            itemStyle={{ 
              padding: '4px 0',
              color: '#475569'
            }}
            formatter={(value, name) => [formatInterest(value), name]}
            separator=": "
            cursor={{ stroke: '#94a3b8', strokeWidth: 1, strokeDasharray: '5 5' }}
          />
          <Legend 
            wrapperStyle={{ 
              fontSize: '12px',
              paddingTop: '20px',
              fontWeight: 500
            }}
            iconType="circle"
            formatter={(value) => {
              const trend = topTrends.find(t => (t.keyword || t.topic) === value);
              return trend ? (trend.keyword || trend.topic) : value;
            }}
          />
          {topTrends.map((trend, index) => {
            const keyword = trend.keyword || trend.topic || 'Unknown';
            const color = colors[index % colors.length];
            return (
              <Area
                key={keyword}
                type="monotone"
                dataKey={keyword}
                stroke={color.stroke}
                strokeWidth={2.5}
                fillOpacity={1}
                fill={`url(#gradient${index})`}
                dot={false}
                activeDot={{ 
                  r: 5, 
                  fill: color.stroke,
                  stroke: 'white',
                  strokeWidth: 2
                }}
                animationDuration={800}
                animationEasing="ease-out"
              />
            );
          })}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export default TrendChart;

