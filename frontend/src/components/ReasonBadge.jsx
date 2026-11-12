import React from 'react';
import { Brain, Users, Sparkles, Flame, ThumbsUp } from 'lucide-react';

export default function ReasonBadge({ reason }) {
  if (!reason) return null;

  const lowerReason = reason.toLowerCase();

  let badgeClass = 'badge-teal';
  let IconComponent = Brain;

  if (lowerReason.includes('preference') || lowerReason.includes('content') || lowerReason.includes('cuisine')) {
    badgeClass = 'badge-teal';
    IconComponent = Brain;
  } else if (lowerReason.includes('people like you') || lowerReason.includes('collaborative') || lowerReason.includes('similar user') || lowerReason.includes('community')) {
    badgeClass = 'badge-blue';
    IconComponent = Users;
  } else if (lowerReason.includes('personalized') || lowerReason.includes('hybrid') || lowerReason.includes('perfect match') || lowerReason.includes('top pick')) {
    badgeClass = 'badge-gold';
    IconComponent = Sparkles;
  } else if (lowerReason.includes('trending') || lowerReason.includes('popular') || lowerReason.includes('hot')) {
    badgeClass = 'badge-orange';
    IconComponent = Flame;
  } else {
    badgeClass = 'badge-teal';
    IconComponent = ThumbsUp;
  }

  return (
    <span className={`badge ${badgeClass} animate-fade-in`} style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
      <IconComponent size={13} />
      <span>{reason}</span>
    </span>
  );
}
