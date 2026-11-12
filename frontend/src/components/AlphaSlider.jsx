import React from 'react';
import { Sliders, RotateCcw, Sparkles } from 'lucide-react';

export default function AlphaSlider({ value, onChange }) {
  const isAuto = value === undefined || value === null;
  const currentVal = isAuto ? 0.5 : Number(value);

  const handleSliderChange = (e) => {
    const val = parseFloat(e.target.value);
    onChange(val);
  };

  const handleResetAuto = () => {
    onChange(undefined);
  };

  return (
    <div className="glass-panel" style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sliders size={18} style={{ color: 'var(--accent-teal)' }} />
          <span style={{ fontWeight: '700', fontSize: '0.9rem', color: 'var(--text-primary)' }}>
            Recommendation Style
          </span>
        </div>

        {isAuto ? (
          <span className="badge badge-teal" title="System automatically balances your preferences vs crowd wisdom based on rating history">
            <Sparkles size={11} /> Auto (Adaptive)
          </span>
        ) : (
          <button
            type="button"
            onClick={handleResetAuto}
            className="btn btn-ghost btn-sm"
            style={{ fontSize: '0.75rem', padding: '2px 8px', height: 'auto', gap: '4px' }}
            title="Reset to adaptive automatic alpha"
          >
            <RotateCcw size={12} /> Auto
          </button>
        )}
      </div>

      <div>
        <input
          type="range"
          min="0"
          max="1"
          step="0.05"
          value={currentVal}
          onChange={handleSliderChange}
          aria-label="Recommendation Alpha Weight"
        />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
          <span style={{ color: currentVal > 0.5 ? 'var(--accent-teal)' : 'inherit', fontWeight: currentVal > 0.5 ? '600' : 'normal' }}>
            🔍 Content-Based
          </span>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            {Math.round(currentVal * 100)}% Taste
          </span>
        </div>

        <div style={{ textAlign: 'center' }}>
          <span className="badge badge-outline" style={{ fontSize: '0.72rem', padding: '2px 8px' }}>
            α = {isAuto ? 'Auto' : currentVal.toFixed(2)}
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
          <span style={{ color: currentVal < 0.5 ? 'var(--accent-gold)' : 'inherit', fontWeight: currentVal < 0.5 ? '600' : 'normal' }}>
            👥 Collaborative
          </span>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            {Math.round((1 - currentVal) * 100)}% Crowd
          </span>
        </div>
      </div>
    </div>
  );
}
