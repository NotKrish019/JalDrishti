import React, { useMemo } from 'react';
import { STEPWELL, WATER_Y, terraceRadius, terraceY } from '../../scene/stepwellSpec';

export interface StepwellSectionProps {
  tone?: 'light' | 'dark';
  showLabels?: boolean;
  className?: string;
  title?: string;
}

const S = 10; // px per metre
const PAD_X = 9;
const LABEL_MARGIN = 150; // px either side for annotation text
const TOP = 6;
const BOTTOM = WATER_Y - 4;

const X = (m: number) => (m + STEPWELL.rimRadius + PAD_X) * S;
const Y = (m: number) => (TOP - m) * S;

/**
 * Section A–A through the illustrative stepwell, drawn from the same
 * dimensions as the 3D model so the drawing and the descent always agree.
 */
export const StepwellSection: React.FC<StepwellSectionProps> = ({
  tone = 'light',
  showLabels = true,
  className = '',
  title = 'Section through an illustrative circular stepwell',
}) => {
  const ink = tone === 'light' ? '#17140F' : '#E2D3BA';
  const faint = tone === 'light' ? 'rgba(23,20,15,0.35)' : 'rgba(226,211,186,0.35)';
  const earth = tone === 'light' ? 'rgba(124,95,64,0.10)' : 'rgba(205,179,143,0.07)';
  const water = tone === 'light' ? '#2F6152' : '#4F8070';

  const width = (STEPWELL.rimRadius + PAD_X) * 2 * S;
  const height = (TOP - BOTTOM) * S;

  const { profile, half } = useMemo(() => {
    // Right half of the stepped profile, from the rim inward and down.
    const pts: [number, number][] = [[STEPWELL.rimRadius + PAD_X, 0], [STEPWELL.rimRadius, 0]];
    for (let k = 0; k < STEPWELL.terraceCount; k += 1) {
      const r = terraceRadius(k);
      pts.push([r, terraceY(k + 1)]);
      pts.push([terraceRadius(k + 1), terraceY(k + 1)]);
    }
    const floor = WATER_Y - 1.6;
    pts.push([terraceRadius(STEPWELL.terraceCount), floor]);
    const left = pts.map(([x, y]) => [-x, y] as [number, number]).reverse();
    const all = [...left, ...pts];
    const d = all.map(([x, y], i) => `${i ? 'L' : 'M'}${X(x).toFixed(1)} ${Y(y).toFixed(1)}`).join(' ');
    return { profile: d, half: pts };
  }, []);

  const earthPath = `${profile} L${X(STEPWELL.rimRadius + PAD_X)} ${Y(BOTTOM)} L${X(-STEPWELL.rimRadius - PAD_X)} ${Y(BOTTOM)} Z`;
  const shaftR = terraceRadius(STEPWELL.terraceCount);
  const monsoonY = terraceY(5) - 0.6;
  const monsoonR = terraceRadius(5);

  const label = (x: number, y: number, lx: number, ly: number, text: string, anchor: 'start' | 'end' = 'start') => (
    <g>
      <path d={`M${X(x)} ${Y(y)} L${X(lx)} ${Y(ly)}`} stroke={faint} strokeWidth="1" fill="none" />
      <circle cx={X(x)} cy={Y(y)} r="2.4" fill={ink} />
      <text
        x={X(lx) + (anchor === 'start' ? 6 : -6)}
        y={Y(ly) + 4}
        textAnchor={anchor}
        fontFamily="IBM Plex Mono, monospace"
        fontSize="11"
        letterSpacing="0.08em"
        fill={ink}
      >
        {text.toUpperCase()}
      </text>
    </g>
  );

  return (
    <svg
      viewBox={showLabels ? `${-LABEL_MARGIN} 0 ${width + LABEL_MARGIN * 2} ${height}` : `0 0 ${width} ${height}`}
      className={className}
      role="img"
      aria-label={`${title}: stepped terraces descend in rings to a carved shaft; the water level rises after the monsoon and falls in the dry season.`}
    >
      <title>{title}</title>
      <defs>
        <pattern id={`hatch-${tone}`} width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="8" stroke={faint} strokeWidth="0.8" />
        </pattern>
      </defs>

      {/* Earth */}
      <path d={earthPath} fill={earth} />
      <path d={earthPath} fill={`url(#hatch-${tone})`} opacity="0.5" />

      {/* Dry-season water */}
      <rect x={X(-shaftR)} y={Y(WATER_Y)} width={shaftR * 2 * S} height={1.6 * S} fill={water} opacity="0.9" />

      {/* Monsoon level (illustrative) */}
      <path
        d={`M${X(-monsoonR)} ${Y(monsoonY)} L${X(monsoonR)} ${Y(monsoonY)}`}
        stroke={water}
        strokeWidth="1.5"
        strokeDasharray="6 5"
      />

      {/* Galleries: columns and roof slabs */}
      {STEPWELL.galleryTiers.map((k) =>
        [-1, 1].map((side) => {
          const cx = side * (terraceRadius(k) + 0.45);
          const outer = side * terraceRadius(k - 1);
          const floor = terraceY(k);
          const top = floor + STEPWELL.galleryHeight;
          return (
            <g key={`${k}-${side}`} stroke={ink} strokeWidth="1.2" fill="none">
              <rect x={X(cx) - 2} y={Y(top)} width="4" height={STEPWELL.galleryHeight * S} fill={ink} stroke="none" />
              <path d={`M${X(cx - side * 0.3)} ${Y(top)} L${X(outer)} ${Y(top)}`} strokeWidth="3" />
            </g>
          );
        }),
      )}

      {/* Stair flights shown in elevation on the far wall */}
      {[1, 3, 5, 7].map((k) => {
        const floor = terraceY(k);
        const x0 = -terraceRadius(k - 1) + 2.4;
        const steps = 9;
        const d = Array.from({ length: steps }, (_, i) => {
          const x = x0 + i * 0.42;
          const y = floor + (i + 1) * (STEPWELL.tierHeight / steps);
          return `M${X(x)} ${Y(y)} h${0.42 * S}`;
        }).join(' ');
        return <path key={k} d={d} stroke={faint} strokeWidth="1" />;
      })}

      {/* Profile */}
      <path d={profile} fill="none" stroke={ink} strokeWidth="1.6" strokeLinejoin="miter" />

      {/* Ground line */}
      <path d={`M0 ${Y(0)} L${width} ${Y(0)}`} stroke={faint} strokeWidth="1" strokeDasharray="2 4" />

      {showLabels && (
        <g>
          {label(-STEPWELL.rimRadius - 4, 0, -STEPWELL.rimRadius - 4, 4, 'Ground level')}
          {label(terraceRadius(4) + 0.45, terraceY(4) + 1.2, STEPWELL.rimRadius - 2, terraceY(2) + 1, 'Colonnaded gallery', 'end')}
          {label(half[6][0] - 0.8, half[6][1], STEPWELL.rimRadius + 4, terraceY(3) - 1, 'Terrace')}
          {label(-terraceRadius(6) + 2.6, terraceY(7) + 1.6, -STEPWELL.rimRadius - 4, terraceY(7) + 1, 'Stair flight')}
          {label(shaftR, terraceY(STEPWELL.terraceCount) - 1.5, STEPWELL.rimRadius + 4, terraceY(8) - 2.5, 'Carved shaft')}
          {label(monsoonR - 1, monsoonY, STEPWELL.rimRadius + 4, monsoonY - 0.4, 'Post-monsoon level')}
          {label(-shaftR + 1, WATER_Y, -STEPWELL.rimRadius - 4, WATER_Y - 1.5, 'Dry-season water')}
        </g>
      )}
    </svg>
  );
};

export default StepwellSection;
