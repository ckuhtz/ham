# Ham workflows

## Hound

```mermaid
flowchart TD;
    A(Start) --> A0{Radio integration?};
    A0 -->|Yes| A1(Ping rigctld);
    A1 --> B0;
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
    A(Start) -->|Send CQ| B{Lookup?};
    B -->|Yes| C(Request Lookup);
    B -->|No| D;
```
