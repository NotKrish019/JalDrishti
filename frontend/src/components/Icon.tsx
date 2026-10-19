import React from 'react';

/** Single-weight (1.5) line icons used across the application UI. */
const PATHS = {
  upload: 'M12 15V4m0 0L7.5 8.5M12 4l4.5 4.5M4.5 15v3.75A1.25 1.25 0 0 0 5.75 20h12.5a1.25 1.25 0 0 0 1.25-1.25V15',
  image:
    'M4.75 5h14.5c.41 0 .75.34.75.75v12.5c0 .41-.34.75-.75.75H4.75a.75.75 0 0 1-.75-.75V5.75c0-.41.34-.75.75-.75ZM4 15.5l4.2-4.2a1 1 0 0 1 1.4 0L14 15.7m-1.5-1.5 1.7-1.7a1 1 0 0 1 1.4 0L20 16.9M15.5 9.25a1.25 1.25 0 1 1-2.5 0 1.25 1.25 0 0 1 2.5 0Z',
  check: 'm5 12.5 4.5 4.5L19 7.5',
  close: 'M6 6l12 12M18 6 6 18',
  alert: 'M12 9v4m0 3.25v.01M10.3 4.2 3.2 17a2 2 0 0 0 1.73 3h14.14A2 2 0 0 0 20.8 17L13.7 4.2a1.95 1.95 0 0 0-3.4 0Z',
  arrowRight: 'M5 12h14m0 0-5.5-5.5M19 12l-5.5 5.5',
  arrowLeft: 'M19 12H5m0 0 5.5-5.5M5 12l5.5 5.5',
  trash: 'M5 7h14M10 11v6m4-6v6M6.5 7l.8 11.2A2 2 0 0 0 9.3 20h5.4a2 2 0 0 0 2-1.8L17.5 7M9.5 7V5a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v2',
  printer: 'M7 9V4h10v5M7 17H5a1 1 0 0 1-1-1v-6a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1h-2M7 14h10v6H7v-6Z',
  menu: 'M4 7h16M4 12h16M4 17h16',
  refresh: 'M19.5 12a7.5 7.5 0 1 1-2.2-5.3M19.5 4.5v4h-4',
  crop: 'M7 3v14h14M3 7h14v14',
  book: 'M5 4.75A1.75 1.75 0 0 1 6.75 3H19v15H6.75A1.75 1.75 0 0 0 5 19.75m0-15v15m0 0A1.75 1.75 0 0 0 6.75 21H19',
  external: 'M14 4h6v6m0-6-8.5 8.5M18 14v4.25c0 .97-.78 1.75-1.75 1.75h-10.5C4.78 20 4 19.22 4 18.25V7.75C4 6.78 4.78 6 5.75 6H10',
} as const;

export type IconName = keyof typeof PATHS;

export interface IconProps {
  name: IconName;
  className?: string;
  title?: string;
}

export const Icon: React.FC<IconProps> = ({ name, className = 'h-4 w-4', title }) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden={title ? undefined : true}
    role={title ? 'img' : undefined}
  >
    {title && <title>{title}</title>}
    <path d={PATHS[name]} />
  </svg>
);
