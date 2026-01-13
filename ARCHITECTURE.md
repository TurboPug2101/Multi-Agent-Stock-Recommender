# Architecture & Flow Diagrams

This document provides detailed architecture diagrams and flow charts for the AI Swing Trader system.

## System Architecture Overview

```mermaid
graph TB
    subgraph "Client Layer"
        User[User/Client]
        Frontend[Frontend UI - Optional]
    end
    
    subgraph "API Layer"
        API[FastAPI Server<br/>Port 8000]
        Endpoints[API Endpoints<br/>/dag/execute<br/>/health<br/>/executions]
    end
    
    subgraph "Orchestration Layer"
        Orch[Orchestrator<br/>DAG Engine]
        DAGConfig[DAG Configuration<br/>dag.py]
        ExecState[Execution State<br/>Tracking]
    end
    
    subgraph "Agent Layer"
        Scout[Scouting Agent<br/>Stock Screening]
        Tech[Technical Agent<br/>Technical Analysis]
        Sent[Sentiment Agent<br/>Sentiment Analysis]
        Strat[Strategist Agent<br/>Decision Making]
    end
    
    subgraph "Data Layer"
        Cache[Cache Layer<br/>3-hour TTL]
        DataProv[Data Providers<br/>Yahoo Finance<br/>Mock Data]
    end
    
    subgraph "External Services"
        Groq[Groq API<br/>LLM Inference]
        NewsAPI[Event Registry<br/>News API]
        GNews[GNews API<br/>Alternative News]
        Reddit[Reddit API<br/>Social Sentiment]
        Twitter[Twitter API<br/>WIP]
        Kite[Zerodha Kite<br/>Trading API]
    end
    
    subgraph "Tool Registry"
        ToolReg[Tool Registry<br/>Dynamic Tool Selection]
        NewsTool[fetch_news]
        GNewsTool[fetch_gnews]
        RedditTool[fetch_reddit]
        TwitterTool[fetch_twitter]
    end
    
    User --> Frontend
    Frontend --> API
    User --> API
    API --> Orch
    Orch --> DAGConfig
    Orch --> ExecState
    
    Orch --> Scout
    Orch --> Tech
    Orch --> Sent
    Orch --> Strat
    
    Scout --> Cache
    Scout --> DataProv
    Tech --> DataProv
    Sent --> Cache
    Sent --> ToolReg
    Strat --> Groq
    Strat --> Kite
    
    ToolReg --> NewsTool
    ToolReg --> GNewsTool
    ToolReg --> RedditTool
    ToolReg --> TwitterTool
    
    NewsTool --> NewsAPI
    GNewsTool --> GNews
    RedditTool --> Reddit
    TwitterTool --> Twitter
    
    Sent --> Groq
    
    style Scout fill:#e1f5ff
    style Tech fill:#fff4e1
    style Sent fill:#ffe1f5
    style Strat fill:#e1ffe1
    style Cache fill:#f0f0f0
    style ToolReg fill:#fffacd
```

## Detailed Agent Execution Flow

```mermaid
flowchart TD
    Start([Start Execution]) --> Init[Initialize Orchestrator]
    Init --> LoadDAG[Load DAG Configuration]
    LoadDAG --> ParseNodes[Parse Agent Nodes]
    ParseNodes --> CheckDeps[Check Dependencies]
    
    CheckDeps --> ScoutNode[Scouting Agent Node]
    ScoutNode --> ScoutExec[Execute Scouting Agent]
    
    ScoutExec --> ScoutCache{Cache<br/>Check}
    ScoutCache -->|Hit| ScoutCached[Return Cached Result]
    ScoutCache -->|Miss| ScoutRun[Run Scouting Logic]
    
    ScoutRun --> ScoutFetch[Fetch Nifty 50 Stocks]
    ScoutFetch --> ScoutScreen[Screen Stocks<br/>Liquidity, Volume, ATR]
    ScoutScreen --> ScoutRank[Rank & Shortlist]
    ScoutRank --> ScoutStore[Store in Cache]
    ScoutStore --> ScoutOut[Shortlisted Stocks]
    ScoutCached --> ScoutOut
    
    ScoutOut --> TechNode[Technical Agent Node]
    ScoutOut --> SentNode[Sentiment Agent Node]
    
    TechNode --> TechExec[Execute Technical Agent]
    TechExec --> TechFetch[Fetch Stock Data]
    TechFetch --> TechCalc[Calculate Indicators<br/>RSI, MACD, MA]
    TechCalc --> TechSignal[Generate Signals]
    TechSignal --> TechOut[Technical Output]
    
    SentNode --> SentExec[Execute Sentiment Agent]
    SentExec --> SentInit[Initialize Tool Registry]
    SentInit --> SentReason[Reason About Data<br/>Sufficiency]
    
    SentReason --> SentPlan[Create Data Collection Plan]
    SentPlan --> SentSelect[Select Tool]
    
    SentSelect --> SentNews[Try News API]
    SentNews --> SentCheck{Data<br/>Sufficient?}
    SentCheck -->|No| SentExpand{Expand<br/>Timeframe?}
    SentExpand -->|Yes| SentExpand90[Expand to 90 days]
    SentExpand90 --> SentCheck
    SentExpand -->|Yes| SentExpand180[Expand to 180 days]
    SentExpand180 --> SentCheck
    SentCheck -->|No| SentAlt[Try Alternative Source]
    SentAlt --> SentGNews[Try GNews API]
    SentGNews --> SentCheck
    SentAlt --> SentSocial[Try Social Media]
    SentSocial --> SentReddit[Fetch Reddit]
    SentReddit --> SentCheck
    SentCheck -->|Yes| SentAnalyze[Analyze Sentiment<br/>via Groq LLM]
    
    SentAnalyze --> SentCache{Cache<br/>Check}
    SentCache -->|Hit| SentCached[Return Cached]
    SentCache -->|Miss| SentStore[Store in Cache]
    SentStore --> SentOut[Sentiment Output]
    SentCached --> SentOut
    
    TechOut --> StratNode[Strategist Agent Node]
    SentOut --> StratNode
    
    StratNode --> StratExec[Execute Strategist Agent]
    StratExec --> StratCombine[Combine Signals<br/>Technical + Sentiment]
    StratCombine --> StratLLM[Groq LLM Reasoning]
    StratLLM --> StratDecision[Generate Trading Decision]
    
    StratDecision --> StratConf{Confidence<br/>> 75%?}
    StratConf -->|Yes| StratExecute[Execute Order<br/>via Kite API]
    StratConf -->|No| StratHold[Hold/No Action]
    
    StratExecute --> StratResult[Order Confirmation]
    StratHold --> StratResult
    StratResult --> End([End])
    
    style ScoutNode fill:#e1f5ff
    style TechNode fill:#fff4e1
    style SentNode fill:#ffe1f5
    style StratNode fill:#e1ffe1
    style StratExecute fill:#ffcccc
```

## Sentiment Agent Agentic Workflow

```mermaid
stateDiagram-v2
    [*] --> Initialize: Agent Started
    Initialize --> ToolRegistry: Register Tools
    ToolRegistry --> Reason: Tools Ready
    
    Reason --> Evaluate: Check Data Needs
    Evaluate --> Plan: Determine Strategy
    
    Plan --> SelectTool: Choose Tool
    SelectTool --> FetchNews: Primary: News API
    SelectTool --> FetchGNews: Alternative: GNews
    SelectTool --> FetchReddit: Social: Reddit
    SelectTool --> FetchTwitter: Social: Twitter (WIP)
    
    FetchNews --> CheckVolume: Data Retrieved
    FetchGNews --> CheckVolume
    FetchReddit --> CheckVolume
    FetchTwitter --> CheckVolume
    
    CheckVolume --> LowVolume: Volume < Threshold
    CheckVolume --> Sufficient: Volume >= Threshold
    
    LowVolume --> ExpandTimeframe: Expand Search
    ExpandTimeframe --> FetchNews: Try 90 days
    ExpandTimeframe --> FetchGNews: Try Alternative
    ExpandTimeframe --> FetchReddit: Try Social
    
    Sufficient --> Analyze: Data Sufficient
    Analyze --> LLMReasoning: Sentiment Analysis
    LLMReasoning --> CacheResult: Store Result
    CacheResult --> [*]: Complete
    
    note right of ToolRegistry
        Tools Available:
        - fetch_news
        - fetch_gnews
        - fetch_reddit
        - fetch_twitter
    end note
    
    note right of ExpandTimeframe
        Adaptive Behavior:
        2 days → 90 days → 180 days
    end note
```

## Data Flow Diagram

```mermaid
graph LR
    subgraph "Input"
        InitInput[Initial Input<br/>top_n: 10]
    end
    
    subgraph "Scouting Agent"
        ScoutIn[Input]
        ScoutOut[Output:<br/>shortlisted_stocks]
    end
    
    subgraph "Technical Agent"
        TechIn[Input:<br/>stocks]
        TechOut[Output:<br/>technical_signals]
    end
    
    subgraph "Sentiment Agent"
        SentIn[Input:<br/>stocks]
        SentTools[Tools:<br/>News, GNews, Reddit]
        SentLLM[Groq LLM]
        SentOut[Output:<br/>sentiment_scores]
    end
    
    subgraph "Strategist Agent"
        StratIn[Input:<br/>technical + sentiment]
        StratLLM[Groq LLM<br/>Decision Making]
        StratOut[Output:<br/>trading_decisions]
    end
    
    subgraph "Execution"
        KiteExec[Kite API<br/>Order Execution]
    end
    
    InitInput --> ScoutIn
    ScoutOut --> TechIn
    ScoutOut --> SentIn
    TechOut --> StratIn
    SentOut --> StratIn
    StratOut --> KiteExec
    
    SentIn --> SentTools
    SentTools --> SentLLM
    SentLLM --> SentOut
    
    StratIn --> StratLLM
    StratLLM --> StratOut
    
    style ScoutOut fill:#e1f5ff
    style TechOut fill:#fff4e1
    style SentOut fill:#ffe1f5
    style StratOut fill:#e1ffe1
    style KiteExec fill:#ffcccc
```

## Caching Strategy

```mermaid
graph TD
    AgentCall[Agent Method Called] --> GenKey[Generate Cache Key<br/>prefix + kwargs]
    GenKey --> CheckCache{Key in<br/>Cache?}
    
    CheckCache -->|Yes| CheckTTL{TTL Valid?<br/>< 3 hours}
    CheckCache -->|No| Execute[Execute Agent Logic]
    
    CheckTTL -->|Yes| ReturnCache[Return Cached Data]
    CheckTTL -->|No| Expire[Expire Cache Entry]
    Expire --> Execute
    
    Execute --> StoreCache[Store Result in Cache]
    StoreCache --> ReturnResult[Return Result]
    ReturnCache --> End([End])
    ReturnResult --> End
    
    style CheckCache fill:#fff4e1
    style CheckTTL fill:#ffe1f5
    style StoreCache fill:#e1ffe1
```

## Error Handling & Retry Logic

```mermaid
graph TD
    AgentExec[Agent Execution] --> Try[Try Execute]
    Try --> Success{Success?}
    
    Success -->|Yes| Return[Return Result]
    Success -->|No| ErrorType{Error Type?}
    
    ErrorType -->|API Error| Retry{Retries<br/>< 3?}
    ErrorType -->|Validation Error| LogError[Log Error]
    ErrorType -->|Network Error| Retry
    
    Retry -->|Yes| Wait[Wait & Retry]
    Wait --> Try
    Retry -->|No| LogError
    
    LogError --> Fallback{Fallback<br/>Available?}
    Fallback -->|Yes| UseFallback[Use Fallback]
    Fallback -->|No| ReturnError[Return Error]
    
    UseFallback --> Return
    ReturnError --> End([End])
    Return --> End
    
    style Retry fill:#fff4e1
    style Fallback fill:#e1ffe1
    style LogError fill:#ffcccc
```

## Component Interaction Sequence

```mermaid
sequenceDiagram
    autonumber
    participant Client
    participant API as FastAPI
    participant Orch as Orchestrator
    participant Cache
    participant Scout as Scouting Agent
    participant Tech as Technical Agent
    participant Sent as Sentiment Agent
    participant Strat as Strategist Agent
    participant Groq
    participant Kite
    
    Client->>API: POST /dag/execute
    API->>Orch: create_orchestrator()
    Orch->>Orch: Load DAG config
    
    Orch->>Scout: execute()
    Scout->>Cache: get(cache_key)
    alt Cache Hit
        Cache-->>Scout: cached_data
    else Cache Miss
        Scout->>Scout: screen_stocks()
        Scout->>Cache: set(cache_key, result)
    end
    Scout-->>Orch: shortlisted_stocks
    
    par Parallel Execution
        Orch->>Tech: execute(stocks)
        Tech->>Tech: analyze_technical()
        Tech-->>Orch: technical_signals
    and
        Orch->>Sent: execute(stocks)
        Sent->>Sent: _collect_data_agentically()
        Sent->>Sent: _reason_about_data_sufficiency()
        Sent->>Sent: _execute_plan()
        loop Until sufficient
            Sent->>Sent: fetch_news/gnews/reddit()
        end
        Sent->>Groq: analyze_sentiment()
        Groq-->>Sent: sentiment_score
        Sent->>Cache: set(cache_key, result)
        Sent-->>Orch: sentiment_scores
    end
    
    Orch->>Strat: execute(technical, sentiment)
    Strat->>Groq: make_decision()
    Groq-->>Strat: trading_decisions
    
    alt High Confidence
        Strat->>Kite: execute_order()
        Kite-->>Strat: order_confirmation
    end
    
    Strat-->>Orch: final_results
    Orch-->>API: execution_result
    API-->>Client: JSON response
```

## Agent Factory Pattern

```mermaid
graph TD
    Orch[Orchestrator] --> LoadAgent[Load Agent Module]
    LoadAgent --> CheckFactory{Has create_agent<br/>Function?}
    
    CheckFactory -->|Yes| CallFactory[Call create_agent<br/>with config]
    CheckFactory -->|No| DirectInit[Direct Class<br/>Instantiation]
    
    CallFactory --> Factory[Factory Function]
    Factory --> Config[Apply Configuration]
    Config --> Create[Create Agent Instance]
    
    DirectInit --> Create
    Create --> Return[Return Agent]
    Return --> Use[Use Agent]
    
    style Factory fill:#e1ffe1
    style Create fill:#fff4e1
```

---

**Note**: These diagrams are best viewed in a Markdown viewer that supports Mermaid (e.g., GitHub, GitLab, VS Code with Mermaid extension, or online Mermaid editors).
