# Frontend Components Reference

Reference for Stock Buddy's React frontend architecture and signal display components.

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [State Management](#state-management)
- [API Integration](#api-integration)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Styling](#styling)

## Overview

Stock Buddy uses Next.js 14 (App Router) with React 18 for the frontend. The application displays trading signals received from TTE in a clean, user-friendly interface integrated with a chat system.

**Key Features**:
- Real-time signal display with level-based coloring
- Filtering by level, direction, symbol
- Pagination for large signal sets
- Chat interface integration
- Responsive design (mobile-friendly)

## Tech Stack

| Technology | Purpose | Version |
|------------|---------|---------|
| **Next.js** | React framework (App Router) | 14.x |
| **React** | UI library | 18.x |
| **TypeScript** | Type safety | 5.x |
| **Redux Toolkit** | State management | Latest |
| **RTK Query** | Data fetching and caching | Latest |
| **Tailwind CSS** | Styling | 3.x |
| **Vercel** | Deployment | - |

## Project Structure

```
src/
├── app/
│   ├── api/tte/          # API routes (webhooks, queries)
│   ├── page.tsx          # Homepage
│   └── layout.tsx        # Root layout
├── components/
│   ├── signals/          # Signal display components
│   └── ui/               # Reusable UI components
├── lib/
│   ├── redux/
│   │   ├── api/          # RTK Query API definitions
│   │   └── store.ts      # Redux store configuration
│   ├── tte/
│   │   ├── schemas.ts    # Zod schemas and TypeScript types
│   │   └── collections.ts # MongoDB collection helpers
│   └── mongodb.ts        # MongoDB client
└── styles/
    └── globals.css       # Global styles and Tailwind config
```

## State Management

### Redux Toolkit Store

Stock Buddy uses Redux Toolkit for global state management with RTK Query for server state.

**Store Configuration**: `src/lib/redux/store.ts`

```typescript
import { configureStore } from '@reduxjs/toolkit';
import { signalsApi } from './api/signalsApi';

export const store = configureStore({
  reducer: {
    [signalsApi.reducerPath]: signalsApi.reducer,
    // Other reducers...
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(signalsApi.middleware),
});
```

### Redux Provider

**Root Layout**: `src/app/layout.tsx`

```typescript
import { Providers } from '@/lib/redux/provider';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

## API Integration

### RTK Query API

Stock Buddy uses RTK Query for declarative data fetching with automatic caching, refetching, and error handling.

**API Definition**: `src/lib/redux/api/signalsApi.ts` (example structure)

```typescript
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export const signalsApi = createApi({
  reducerPath: 'signalsApi',
  baseQuery: fetchBaseQuery({ baseUrl: '/api/tte' }),
  tagTypes: ['Signals', 'HotSymbols', 'Stats'],
  endpoints: (builder) => ({
    // Get signals with filtering
    getSignals: builder.query({
      query: (params) => ({
        url: '/signals',
        params: {
          limit: params.limit || 50,
          offset: params.offset || 0,
          level: params.level,
          direction: params.direction,
          symbol: params.symbol,
        },
      }),
      providesTags: ['Signals'],
    }),

    // Get hot symbols
    getHotSymbols: builder.query({
      query: (limit = 8) => `/hot-symbols?limit=${limit}`,
      providesTags: ['HotSymbols'],
    }),

    // Get statistics
    getStats: builder.query({
      query: (hours = 24) => `/stats?hours=${hours}`,
      providesTags: ['Stats'],
    }),

    // Update signal (screenshot URL)
    updateSignal: builder.mutation({
      query: ({ id, ...patch }) => ({
        url: `/signals/${id}`,
        method: 'PATCH',
        body: patch,
      }),
      invalidatesTags: ['Signals'],
    }),
  }),
});

export const {
  useGetSignalsQuery,
  useGetHotSymbolsQuery,
  useGetStatsQuery,
  useUpdateSignalMutation,
} = signalsApi;
```

### Query Hooks Usage

**In Components**:

```typescript
import { useGetSignalsQuery } from '@/lib/redux/api/signalsApi';

export function SignalsList() {
  const { data, isLoading, error } = useGetSignalsQuery({
    limit: 20,
    level: 3,
    direction: 'bullish',
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <div>
      {data.signals.map(signal => (
        <SignalCard key={signal._id} signal={signal} />
      ))}
    </div>
  );
}
```

## Component Architecture

### Component Hierarchy

```
App
└── Layout
    └── Page
        ├── SignalsProvider (Redux)
        └── SignalsContainer
            ├── SignalsFilters
            │   ├── LevelFilter (1/2/3)
            │   ├── DirectionFilter (bullish/bearish)
            │   └── SymbolFilter
            ├── SignalsList
            │   └── SignalCard (repeated)
            │       ├── SignalHeader (symbol, direction, level)
            │       ├── SignalDetails (NWE, OB, DIV info)
            │       └── SignalActions (view chart, etc.)
            └── SignalsPagination
```

### Core Components

#### SignalCard

Displays a single trading signal with level-based styling.

**Props**:
```typescript
interface SignalCardProps {
  signal: TTESignalDocument;
}
```

**Rendering**:
- **Level 1**: Yellow border/badge
- **Level 2**: Orange border/badge
- **Level 3**: Green border/badge

**Display Fields**:
- Symbol name and direction (↑ bullish / ↓ bearish)
- Signal level badge
- NWE timeframes (comma-separated)
- Order block details (if present): type, high/low, timeframe
- Divergence details (if present): type, timeframe
- Timestamp (relative, e.g., "2 hours ago")
- Screenshot link (if available)

#### SignalsFilters

Filter controls for querying signals.

**State** (local or Redux):
```typescript
interface FilterState {
  level: 1 | 2 | 3 | null;
  direction: 'bullish' | 'bearish' | null;
  symbol: string;
  limit: number;
  offset: number;
}
```

**Controls**:
- Level dropdown (All / 1 / 2 / 3)
- Direction toggle (All / Bullish / Bearish)
- Symbol search input (autocomplete)
- Results per page slider

#### SignalsList

Container for signal cards with loading and empty states.

**States**:
- **Loading**: Skeleton loaders or spinner
- **Empty**: "No signals found" message
- **Error**: Error message with retry button
- **Data**: Grid or list of SignalCard components

#### SignalsPagination

Pagination controls for navigating large signal sets.

**Props**:
```typescript
interface PaginationProps {
  total: number;
  limit: number;
  offset: number;
  onPageChange: (newOffset: number) => void;
}
```

**Features**:
- Previous/Next buttons
- Page number display (e.g., "Page 3 of 10")
- Jump to page input
- Results count (e.g., "Showing 21-40 of 234")

## Data Flow

### Complete Data Flow

```
API Endpoint → RTK Query → Redux Store → React Component → UI
     ↓              ↓            ↓              ↓
  MongoDB     Cache Layer   Global State   Local State
```

### Query Flow Example

1. **Component Mount**: `SignalsList` component mounts
2. **Hook Call**: `useGetSignalsQuery({ level: 3 })` executed
3. **Cache Check**: RTK Query checks cache for matching query
4. **API Call**: If cache miss, fetches from `/api/tte/signals?level=3`
5. **Response**: API returns `{ signals: [...], total: 234 }`
6. **Cache Update**: RTK Query updates cache and invalidates related tags
7. **Re-render**: Component re-renders with new data
8. **UI Update**: Signal cards displayed to user

### Mutation Flow Example

1. **User Action**: User clicks "Mark Complete" on signal
2. **Mutation Call**: `updateSignal({ id: '...', status: 'complete' })`
3. **API Call**: PATCH request to `/api/tte/signals/{id}`
4. **Response**: API returns `{ success: true, id: '...' }`
5. **Cache Invalidation**: RTK Query invalidates `['Signals']` tag
6. **Refetch**: All queries with `['Signals']` tag refetch automatically
7. **UI Update**: Signal list updates with new status

### Real-time Updates

Stock Buddy does not currently use WebSockets or real-time updates. Signals are fetched on:
- Initial component mount
- Manual refetch (pull-to-refresh)
- Cache invalidation (after mutations)
- Polling (if configured)

**Future Enhancement**: Add WebSocket support for real-time signal notifications.

## Styling

### Tailwind CSS

Stock Buddy uses Tailwind CSS for utility-first styling.

**Configuration**: `tailwind.config.js`

```javascript
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'signal-level1': '#FCD34D',  // Yellow
        'signal-level2': '#FB923C',  // Orange
        'signal-level3': '#4ADE80',  // Green
        'bullish': '#10B981',
        'bearish': '#EF4444',
      },
    },
  },
  plugins: [],
};
```

### Level-Based Styling

**Signal Levels**:
```typescript
const levelColors = {
  1: 'border-signal-level1 bg-yellow-50',
  2: 'border-signal-level2 bg-orange-50',
  3: 'border-signal-level3 bg-green-50',
};

<div className={`border-2 rounded-lg p-4 ${levelColors[signal.level]}`}>
  {/* Signal content */}
</div>
```

**Direction-Based Styling**:
```typescript
const directionIcons = {
  bullish: '↑',
  bearish: '↓',
};

const directionColors = {
  bullish: 'text-bullish',
  bearish: 'text-bearish',
};

<span className={directionColors[signal.direction]}>
  {directionIcons[signal.direction]} {signal.direction}
</span>
```

### Responsive Design

All components use Tailwind's responsive utilities:

```typescript
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* Signal cards */}
</div>
```

**Breakpoints**:
- `sm`: 640px (mobile)
- `md`: 768px (tablet)
- `lg`: 1024px (desktop)
- `xl`: 1280px (large desktop)

### Dark Mode Support

Stock Buddy supports dark mode via Tailwind's dark mode classes:

```typescript
<div className="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
  {/* Content */}
</div>
```

---

**Related**:
- [API Endpoints](api_endpoints.md) - API endpoints used by RTK Query
- [Database Schema](database_schema.md) - Signal document structure
- [Integration Flow](integration_flow.md) - How signals flow from TTE to frontend
