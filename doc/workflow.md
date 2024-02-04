# Ham workflows

## Hound

```mermaid
flowchart TD;
    A(Start) --> A0{Rig integration?};
    A0 -->|Yes| A1(Ping rigctld);
    A1 --> B0 (Ready);
    A0 -->|No| B0; 
    B0 -->|Find CQ| B1{Worked?};
    B1 -->|Yes| C(Clear);
    B1 -->|No| D(Publish QSO target);
    D -->|Capture QSO metadata| E(Log QSO);
    E -->F(Clear)
```

## Fox

```mermaid
flowchart TD;
    A(Start) --> A0{Rig integration?};
    A0 -->|Yes| A1(Ping rigctld);
    A1 --> B0 (Ready);
    B0 -->|Send CQ| B1{Lookup?};
    B1 -->|Yes| C(Request Lookup);
    B1 -->|No| D;
```
