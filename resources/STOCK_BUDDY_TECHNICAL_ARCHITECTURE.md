# Stock Buddy Technical Architecture

> An AI-powered trading assistant using RAG (Retrieval-Augmented Generation) for intelligent market analysis

---

## System Architecture Overview

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        UI[React Chat Interface]
        Redux[Redux + RTK Query]
    end

    subgraph API["Next.js API Layer"]
        ChatAPI["/api/chat"]
        SignalsAPI["/api/signals"]
        AuthAPI["/api/auth"]
    end

    subgraph AI["AI Services Layer"]
        AIService[AI Service Orchestrator]
        RAG[RAG Response Service]
        Retrieval[Retrieval Service]
        Memory[Conversation Memory]
        Prompts[Prompt Template Service]
    end

    subgraph Data["Data Layer"]
        MongoDB[(MongoDB Atlas)]
        VectorSearch[Vector Search Index]
        SignalsColl[Signals Collection]
        KnowledgeColl[Knowledge Base Collection]
        ConvoColl[Conversations Collection]
    end

    subgraph External["External Services"]
        OpenAI[OpenAI API]
        GPT4[GPT-4o Chat Model]
        Embeddings[text-embedding-3-small]
    end

    UI --> Redux
    Redux --> ChatAPI
    Redux --> SignalsAPI
    ChatAPI --> AIService
    SignalsAPI --> SignalsColl
    AuthAPI --> MongoDB

    AIService --> RAG
    RAG --> Retrieval
    RAG --> Memory
    RAG --> Prompts

    Retrieval --> VectorSearch
    Retrieval --> SignalsColl
    Memory --> ConvoColl

    VectorSearch --> KnowledgeColl
    VectorSearch --> Embeddings

    RAG --> GPT4
    Prompts --> GPT4

    MongoDB --> VectorSearch
    MongoDB --> SignalsColl
    MongoDB --> KnowledgeColl
    MongoDB --> ConvoColl
```

---

## RAG Pipeline Flow

The RAG system combines real-time trading signals with expert knowledge to generate contextual responses.

```mermaid
flowchart LR
    subgraph Input
        Query[User Query]
        Symbol[Trading Symbol]
    end

    subgraph Retrieval["Context Retrieval"]
        direction TB
        Embed[Generate Query Embedding]
        VSearch[Vector Similarity Search]
        SigFetch[Fetch Latest Signals]
        Boost[Apply Financial Term Boost]
    end

    subgraph Augmentation["Context Assembly"]
        direction TB
        History[Load Conversation History]
        Classify[Classify Query Type]
        Template[Select Prompt Template]
        Context[Assemble Full Context]
    end

    subgraph Generation["Response Generation"]
        direction TB
        Prompt[Build System + User Prompts]
        Stream[Stream GPT-4o Response]
        Save[Save to Memory]
    end

    Query --> Embed
    Symbol --> SigFetch
    Embed --> VSearch
    VSearch --> Boost
    Boost --> Context
    SigFetch --> Context

    History --> Context
    Classify --> Template
    Template --> Context

    Context --> Prompt
    Prompt --> Stream
    Stream --> Save
```

---

## Database Architecture

```mermaid
erDiagram
    SIGNALS {
        ObjectId _id PK
        string symbol
        string direction "Buy | Sell"
        string timeframe
        string screener "NW | SB | OB"
        string timestamp
        object info
        string tvEntrySnapshot
        string pngEntrySnapshot
    }

    KNOWLEDGE_BASE {
        ObjectId _id PK
        string content
        float[] embedding "1536 dimensions"
        string title
        string category
        string[] tags
        string filename
        int chunkIndex
    }

    CONVERSATIONS {
        ObjectId _id PK
        string symbol
        string userId
        string role "user | assistant"
        string content
        datetime timestamp
        object metadata
    }

    WATCHLISTS {
        ObjectId _id PK
        string userId
        string[] symbols
        string name
    }

    USERS ||--o{ WATCHLISTS : owns
    USERS ||--o{ CONVERSATIONS : has
    SIGNALS }o--|| SYMBOLS : belongs_to
    CONVERSATIONS }o--|| SYMBOLS : scoped_by
```

---

## Signal Type System

Stock Buddy processes three types of Smart Money Concept (SMC) trading signals:

```mermaid
flowchart TB
    subgraph SignalTypes["Signal Types (Discriminated Union)"]
        direction LR

        subgraph NW["NW Signal"]
            NW_Desc["Nadaraya Watson<br/>Trend Reversal Indicator"]
            NW_Info["info: {} (empty)"]
        end

        subgraph SB["SB Signal"]
            SB_Desc["Structure Break<br/>Market Structure Changes"]
            SB_Info["info: swing points,<br/>zigzag degree"]
        end

        subgraph OB["OB Signal"]
            OB_Desc["Order Block<br/>Institutional Zones"]
            OB_Info["info: high/low prices,<br/>pips, block type"]
        end
    end

    subgraph Validation["Entry Validation Strategy"]
        Check["OB + SB + NW Alignment Check"]
        Dir["Same Direction?"]
        TF["Correct Timeframes?"]
        Entry["Valid Entry Signal"]
    end

    NW --> Check
    SB --> Check
    OB --> Check
    Check --> Dir
    Dir --> TF
    TF --> Entry
```

---

## Knowledge Base Structure

The AI is augmented with expert trading knowledge stored as vector embeddings:

```mermaid
mindmap
    root((Knowledge Base))
        Indicators
            Nadaraya Watson Explanation
            Order Block Identification
            Structure Break Detection
        Strategies
            SMC Entry Rules
            OB→SB→NW Sequence
            Risk Management
        Analysis
            Multi-Timeframe Analysis
            Market Structure
            Institutional Behavior
        Technical
            Chart Patterns
            Price Action
            Volume Analysis
```

### Knowledge Retrieval Process

```mermaid
sequenceDiagram
    participant User
    participant Retrieval as Retrieval Service
    participant Embed as Embedding Service
    participant Vector as Vector Search
    participant Signals as Signals DB

    User->>Retrieval: Query + Symbol
    Retrieval->>Retrieval: Expand Abbreviations<br/>(OB→Order Block, etc.)
    Retrieval->>Embed: Generate Query Embedding
    Embed-->>Retrieval: 1536-dim Vector

    par Parallel Retrieval
        Retrieval->>Vector: Semantic Search
        Vector-->>Retrieval: Relevant Documents
    and
        Retrieval->>Signals: Fetch Latest Signals
        Signals-->>Retrieval: NW, SB, OB Signals
    end

    Retrieval->>Retrieval: Apply Financial Term Boost
    Retrieval->>Retrieval: Deduplicate & Rank
    Retrieval-->>User: Combined Context
```

---

## Conversation Memory Architecture

```mermaid
flowchart TB
    subgraph MemoryLayers["Dual-Layer Memory System"]
        direction LR

        subgraph InMemory["In-Memory Cache"]
            Fast["Fast Access"]
            Limit["Last 50 Messages"]
            PerSymbol["Per Symbol Map"]
        end

        subgraph Persistent["MongoDB Storage"]
            Durable["Persistent Storage"]
            UserScoped["User-Scoped"]
            Paginated["Paginated Retrieval"]
        end
    end

    Write[New Message] --> InMemory
    Write --> Persistent

    Read[Read History] --> InMemory
    InMemory -->|Cache Miss| Persistent
```

---

## Key Features

```mermaid
flowchart LR
    subgraph Core["Core Features"]
        Chat["WhatsApp-Style<br/>Chat Interface"]
        Streaming["Real-Time<br/>Response Streaming"]
        Signals["Live Trading<br/>Signal Display"]
    end

    subgraph Intelligence["AI Intelligence"]
        RAG["RAG-Powered<br/>Responses"]
        Memory["Per-Symbol<br/>Conversation Memory"]
        Strategy["Strategy<br/>Validation"]
    end

    subgraph Data["Data Management"]
        Watchlist["Symbol<br/>Watchlists"]
        Groups["Group Chats<br/>with AI"]
        History["Signal &<br/>Chat History"]
    end

    Core --> Intelligence
    Intelligence --> Data
```

### Feature Summary

| Feature | Description |
|---------|-------------|
| **RAG Chat** | AI responses augmented with trading knowledge and real-time signals |
| **Signal Integration** | NW, SB, OB signals displayed inline with chat |
| **Strategy Validation** | Automatic OB→SB→NW sequence and direction alignment checks |
| **Conversation Memory** | Per-symbol chat history with user scoping |
| **Streaming Responses** | Real-time token-by-token response display |
| **Watchlist Management** | Organize and track multiple trading symbols |
| **Group Chat** | Collaborative trading discussions with AI assistance |
| **Signal Attachments** | Attach signals to messages for context |

---

## Technology Stack

```mermaid
flowchart TB
    subgraph Frontend["Frontend"]
        Next["Next.js 15"]
        React["React 19"]
        Tailwind["Tailwind CSS"]
        Radix["Radix UI"]
        RTK["Redux Toolkit"]
    end

    subgraph Backend["Backend"]
        API["Next.js API Routes"]
        Auth["NextAuth v5"]
        TS["TypeScript"]
    end

    subgraph AI["AI/ML"]
        OpenAI["OpenAI GPT-4o"]
        Embed["text-embedding-3-small"]
    end

    subgraph Database["Database"]
        Mongo["MongoDB Atlas"]
        Vector["Vector Search"]
    end

    Frontend --> Backend
    Backend --> AI
    Backend --> Database
    AI --> Database
```

---

## Request-Response Flow

```mermaid
sequenceDiagram
    participant User
    participant Chat as Chat Window
    participant API as /api/chat
    participant AI as AI Service
    participant RAG as RAG Service
    participant DB as MongoDB

    User->>Chat: "What should I do with EURUSD?"
    Chat->>API: POST (stream=true)
    API->>AI: streamChatResponse()

    AI->>RAG: generateResponse()

    par Context Assembly
        RAG->>DB: Vector Search (Knowledge)
        RAG->>DB: Fetch Latest Signals
        RAG->>DB: Load Conversation History
    end

    RAG->>RAG: Classify Query → "trading_strategy"
    RAG->>RAG: Build Prompt with SMC Context

    loop Streaming
        RAG-->>API: Token Chunk
        API-->>Chat: SSE Event
        Chat-->>User: Display Token
    end

    RAG->>DB: Save to Conversation Memory
    API-->>Chat: {done: true, fullResponse}
```

---

## Security & Scoping

```mermaid
flowchart TB
    subgraph Auth["Authentication"]
        Google["Google OAuth"]
        NextAuth["NextAuth v5"]
        JWT["JWT Sessions"]
    end

    subgraph Scoping["Data Scoping"]
        UserScope["User-Level Isolation"]
        SymbolScope["Symbol-Level Conversations"]
        GroupScope["Group Membership"]
    end

    subgraph Privacy["Privacy"]
        NoLeak["No Cross-User Data Leakage"]
        Isolated["Isolated Conversation Contexts"]
    end

    Auth --> Scoping
    Scoping --> Privacy
```

---

## Performance Optimizations

| Layer | Optimization | TTL/Limit |
|-------|-------------|-----------|
| **Response Cache** | Identical query caching | 15 minutes |
| **Retrieval Cache** | Knowledge search results | 10 minutes |
| **Embedding Cache** | Vector embeddings | FIFO @ 100 items |
| **Signal Cache** | RTK Query auto-cache | 5 minutes |
| **Memory Cache** | In-memory conversations | 50 messages/symbol |

---

## Summary

Stock Buddy implements a production-grade RAG architecture that:

1. **Retrieves** relevant context via MongoDB Vector Search
2. **Augments** queries with SMC trading knowledge and live signals
3. **Generates** responses using GPT-4o with specialized prompts
4. **Remembers** conversations per user and trading symbol
5. **Validates** trading strategies through signal sequence analysis
6. **Streams** responses for optimal user experience
