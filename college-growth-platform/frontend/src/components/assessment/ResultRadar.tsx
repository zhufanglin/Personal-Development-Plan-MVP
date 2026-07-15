'use client';

interface RadarDataPoint {
  dimension: string;
  score: number;
  fullMark?: number;
}

interface ResultRadarProps {
  data: RadarDataPoint[];
  title?: string;
  dark?: boolean;
}

const APPLE_BLUE = '#2997ff';
const APPLE_GREEN = '#30d158';
const APPLE_ORANGE = '#ff9f0a';
const APPLE_RED = '#ff453a';

function getScoreColor(score: number) {
  if (score >= 80) return APPLE_GREEN;
  if (score >= 60) return APPLE_BLUE;
  if (score >= 40) return APPLE_ORANGE;
  return APPLE_RED;
}

export function ResultRadar({ data, title, dark = false }: ResultRadarProps) {
  const size = 300;
  const center = size / 2;
  const radius = 115;
  const levels = 5;
  const fullMark = data[0]?.fullMark ?? 100;

  const angleStep = (Math.PI * 2) / data.length;

  const getPoint = (index: number, value: number) => {
    const angle = angleStep * index - Math.PI / 2;
    const r = (value / fullMark) * radius;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
    };
  };

  const gridPoints = (level: number) => {
    const r = (radius * level) / levels;
    return data
      .map((_, i) => {
        const angle = angleStep * i - Math.PI / 2;
        return `${center + r * Math.cos(angle)},${center + r * Math.sin(angle)}`;
      })
      .join(' ');
  };

  const dataPoints = data
    .map((d, i) => getPoint(i, d.score))
    .map((p) => `${p.x},${p.y}`)
    .join(' ');

  const gridColor = dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)';
  const axisColor = dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)';
  const labelColor = dark ? '#86868b' : '#86868b';

  return (
    <div className="flex flex-col items-center">
      {title && (
        <h3 className={`text-[17px] font-medium mb-4 ${dark ? 'text-[#f5f5f7]' : 'text-[#1d1d1f]'}`}>
          {title}
        </h3>
      )}
      <svg width={size} height={size} className="overflow-visible">
        {/* Grid levels */}
        {Array.from({ length: levels }, (_, i) => (
          <polygon
            key={i}
            points={gridPoints(levels - i)}
            fill="none"
            stroke={gridColor}
            strokeWidth={1}
          />
        ))}
        {/* Axis lines */}
        {data.map((_, i) => {
          const angle = angleStep * i - Math.PI / 2;
          const x2 = center + radius * Math.cos(angle);
          const y2 = center + radius * Math.sin(angle);
          return (
            <line
              key={i}
              x1={center}
              y1={center}
              x2={x2}
              y2={y2}
              stroke={axisColor}
              strokeWidth={1}
            />
          );
        })}
        {/* Data area — gradient fill */}
        <defs>
          <linearGradient id="radarFill" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={APPLE_BLUE} stopOpacity="0.25" />
            <stop offset="100%" stopColor={APPLE_BLUE} stopOpacity="0.08" />
          </linearGradient>
        </defs>
        <polygon
          points={dataPoints}
          fill="url(#radarFill)"
          stroke={APPLE_BLUE}
          strokeWidth={2}
          strokeLinejoin="round"
        />
        {/* Data points */}
        {data.map((d, i) => {
          const p = getPoint(i, d.score);
          return (
            <circle
              key={i}
              cx={p.x}
              cy={p.y}
              r={4.5}
              fill="#fff"
              stroke={APPLE_BLUE}
              strokeWidth={2}
            />
          );
        })}
        {/* Dimension labels */}
        {data.map((d, i) => {
          const angle = angleStep * i - Math.PI / 2;
          const labelR = radius + 24;
          const x = center + labelR * Math.cos(angle);
          const y = center + labelR * Math.sin(angle);
          const anchor = Math.abs(Math.cos(angle)) < 0.1 ? 'middle' : Math.cos(angle) > 0 ? 'start' : 'end';
          return (
            <text
              key={i}
              x={x}
              y={y}
              textAnchor={anchor}
              dominantBaseline="central"
              fill={labelColor}
              fontSize="12"
              fontFamily="-apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif"
            >
              {d.dimension}
            </text>
          );
        })}
      </svg>

      {/* Legend — score list */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-2.5 mt-6 w-full max-w-md">
        {data.map((d, i) => {
          const color = getScoreColor(d.score);
          return (
            <div key={i} className="flex items-center gap-2.5">
              <span
                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: color }}
              />
              <span className={`text-[14px] truncate ${dark ? 'text-[#f5f5f7]' : 'text-[#1d1d1f]'}`}>
                {d.dimension}
              </span>
              <span className="text-[14px] font-semibold ml-auto" style={{ color }}>
                {Math.round(d.score)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

