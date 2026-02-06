/* Traffic Light indicator component */

import React from 'react';

interface TrafficLightProps {
  score: number;
  greenThreshold?: number;
  orangeThreshold?: number;
  size?: 'small' | 'medium' | 'large';
}

export const TrafficLight: React.FC<TrafficLightProps> = ({
  score,
  greenThreshold = 70,
  orangeThreshold = 40,
  size = 'medium'
}) => {
  const getIndicator = (): string => {
    if (score >= greenThreshold) return '🟢';
    if (score >= orangeThreshold) return '🟠';
    return '🔴';
  };

  const getLabel = (): string => {
    if (score >= greenThreshold) return 'Good';
    if (score >= orangeThreshold) return 'Needs Improvement';
    return 'Poor';
  };

  const sizeMap = {
    small: '1.5rem',
    medium: '2rem',
    large: '3rem'
  };

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
      <span style={{ fontSize: sizeMap[size] }}>
        {getIndicator()}
      </span>
      <span style={{ fontSize: size === 'large' ? '1.2rem' : '1rem' }}>
        {getLabel()}
      </span>
    </div>
  );
};
