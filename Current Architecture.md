# Contexture Architecture & Flow Diagrams

## System Architecture Diagram

```mermaid
graph TB
    subgraph Client["Client Layer"]
        CLI["CLI Client"]
        UI["Web UI"]
    end

    subgraph Backend["Backend Services"]
        FastAPI["FastAPI Backend<br/>Port: 8002<br/>client_dynamic_ui.py"]
        OCS["OCS Service<br/>Port: 8000<br/>Go/Gin"]
        MCP["MCP Server<br/>Port: 8001<br/>FastMCP"]
    end

    subgraph DataSources["Data Sources & Connectors"]
        Prometheus["Prometheus<br/>Metrics Collection"]
        MongoDB["MongoDB<br/>Context Storage"]
        Istio["Istio Connector<br/>Topology Detection"]
    end

    subgraph LLM["LLM & Processing"]
        Ollama["Ollama LLM<br/>NLP Processing"]
        DP["Dynamic Prompt<br/>Config Engine"]
    end

    subgraph Spec["Open Context Specification"]
        OCSSpec["OCS Definition<br/>- Identity & Origin<br/>- Dimensionality<br/>- Metric Semantics<br/>- Temporal Context<br/>- Operational Constraints"]
    end

    Client -->|Query| FastAPI
    FastAPI -->|Get OCS Context| OCS
    FastAPI -->|Execute Tools| MCP
    FastAPI -->|Ask| Ollama
    
    OCS -->|Fetch Metrics| Prometheus
    OCS -->|Store/Retrieve Topology| MongoDB
    OCS -->|Query Topology| Istio
    
    MCP -->|Query Metrics| Prometheus
    MCP -->|Execute Monitoring Tools| Prometheus
    
    OCS -->|Generate| OCSSpec
    FastAPI -->|Use| OCSSpec
    
    Ollama -->|Powered by| DP

    style Client fill:#e1f5ff
    style Backend fill:#f3e5f5
    style DataSources fill:#e8f5e9
    style LLM fill:#fff3e0
    style Spec fill:#fce4ec
```

## System Component Interaction Diagram

```mermaid
graph LR
    subgraph RequestProcessing["Request Processing"]
        User["User<br/>Natural Language<br/>Query"]
        ParseQuery["Parse Query<br/>via Ollama"]
        GenerateWorkflow["Generate<br/>Workflow"]
        ExecuteTools["Execute<br/>MCP Tools"]
    end

    subgraph ContextBuilding["Context Building"]
        FetchOCS["Fetch OCS<br/>Prompt"]
        GetTopology["Get Topology<br/>from MongoDB"]
        GetMetrics["Get Current<br/>Metrics"]
        GetPolicies["Get Operational<br/>Policies"]
    end

    subgraph ResponseGeneration["Response Generation"]
        CombineContext["Combine<br/>Context"]
        Summarize["Summarize<br/>Results"]
        ReturnResponse["Return to User"]
    end

    User -->|1| ParseQuery
    ParseQuery -->|2| GenerateWorkflow
    GenerateWorkflow -->|3| ExecuteTools
    
    ExecuteTools -->|4| FetchOCS
    FetchOCS -->|5| GetTopology
    GetTopology -->|6| GetMetrics
    GetMetrics -->|7| GetPolicies
    
    GetPolicies -->|8| CombineContext
    CombineContext -->|9| Summarize
    Summarize -->|10| ReturnResponse

    style User fill:#fff3e0
    style RequestProcessing fill:#e3f2fd
    style ContextBuilding fill:#e8f5e9
    style ResponseGeneration fill:#fce4ec
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant User as User/Client
    participant FA as FastAPI Backend
    participant OCS as OCS Service
    participant Ollama as Ollama LLM
    participant MCP as MCP Server
    participant Prom as Prometheus
    participant MongoDB as MongoDB
    participant Istio as Istio Connector

    User->>FA: Send natural language query
    
    FA->>Ollama: Convert NL to workflow steps
    Ollama-->>FA: Return workflow JSON
    
    FA->>OCS: GET /get_ocs_prompt
    OCS->>MongoDB: Query topology data
    MongoDB-->>OCS: Return saved adjacency lists
    OCS->>Prom: Query metrics config
    Prom-->>OCS: Return metrics
    OCS-->>FA: Return OCS context spec
    
    FA->>MCP: Execute workflow tools
    MCP->>Prom: Query time-series data
    Prom-->>MCP: Return metrics
    MCP-->>FA: Return tool results
    
    FA->>Ollama: Summarize results with OCS context
    Ollama-->>FA: Return summary
    
    FA-->>User: Return results + summary
```

## OCS Service Request Flow

```mermaid
graph TB
    Client["Client"]
    
    Client -->|POST /collect_istio_metrics| Handler["CollectTopology<br/>Handler"]
    
    Handler -->|Parse timestamps| TimeParser["Timestamp<br/>Parser"]
    TimeParser -->|Optional: from/to params<br/>or time_window_minutes| TimeRange["Time Range<br/>Resolved"]
    
    TimeRange -->|Use config workloads| FetchTopology["Istio Connector<br/>FetchTopology"]
    
    FetchTopology -->|Query time-series| Prometheus["Prometheus"]
    Prometheus -->|Istio metrics<br/>request relationships| FetchTopology
    
    FetchTopology -->|Extract workload<br/>relationships| BuildAdjacency["Build Adjacency<br/>List"]
    
    BuildAdjacency -->|Save to collection| MongoDB["MongoDB<br/>Store Repository"]
    
    MongoDB -->|Return doc ID| Handler
    
    Handler -->|Build response| Response["Response JSON<br/>- adjacency_list<br/>- document_id<br/>- timestamps<br/>- connector info"]
    
    Response -->|HTTP 200| Client

    style Client fill:#fff3e0
    style Handler fill:#e3f2fd
    style TimeParser fill:#e3f2fd
    style Prometheus fill:#e8f5e9
    style MongoDB fill:#e8f5e9
    style Response fill:#fce4ec
```

## MCP Server Tool Architecture

```mermaid
graph TB
    MCP["MCP Server<br/>FastMCP"]
    
    MCP -->|Monitoring Tools| Tools["<br/>- current_metric_for_pods<br/>- detect_pod_anomalies<br/>- namespace_resource_summary<br/>- detect_crashloop_pods<br/>- correlate_metrics<br/>- pod_event_timeline<br/>- node_condition_summary<br/>- explain_ocs_policy<br/>"]
    
    Tools -->|Query| Prometheus["Prometheus"]
    Tools -->|Process| Analysis["Anomaly Detection<br/>Correlation<br/>Timeline Analysis<br/>Resource Summary"]
    
    Analysis -->|Return| Results["Tool Results<br/>JSON Format"]
    
    Results -->|Back to Client| MCP

    style MCP fill:#e3f2fd
    style Tools fill:#f3e5f5
    style Prometheus fill:#e8f5e9
    style Analysis fill:#fff3e0
```

## Key Components Summary

### OCS Service (Go, Port 8000)
- **Purpose**: Core context engine that provides OCS specifications
- **Endpoints**:
  - `GET /get_ocs_prompt` - Returns OCS context definitions
  - `POST /collect_istio_metrics` - Collects and stores topology
  - `GET /health` - Health check
- **Dependencies**: Prometheus, MongoDB, Istio
- **Framework**: Gin

### MCP Server (Python, Port 8001)
- **Purpose**: Monitoring tools and context provider for queries
- **Framework**: FastMCP
- **Tools**: Various monitoring and analysis functions
- **Dependencies**: Prometheus, Pandas

### FastAPI Backend (Python, Port 8002)
- **Purpose**: Main API for client interactions and orchestration
- **Endpoints**:
  - `POST /api/query` - Process NL queries
  - `GET /api/config` - Get configuration
  - `GET /health` - Health check
- **Workflow**: Parse → Execute → Summarize

### Open Context Specification (OCS)
Defines operational context with 5 key dimensions:
1. **Identity & Origin**: Unique fingerprint of data source
2. **Dimensionality & Topology**: Relationships between components
3. **Metric Semantics**: What the metrics represent
4. **Temporal Context**: Time-based information (point-in-time vs trend)
5. **Operational Constraints**: Health interpretation (thresholds, polarity, aggregation)

### Data Storage & Integration
- **Prometheus**: Metrics collection and querying
- **MongoDB**: Topology and context storage
- **Istio**: Service mesh topology detection
- **Ollama**: LLM for natural language processing
