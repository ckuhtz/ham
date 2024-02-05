# Ham workflows

Different microservice flows broken down with interactions.

1. [Fox or Hound](#fox-or-hound)
2. [Rig status request](#rig-status-request)
3. [Log QSO request](#log-qso-request)
4. [Query Log request](#query-log-request)
5. [Publish Heartbeat](#publish-heartbeat)



## Workflows

### Fox or Hound

```mermaid
flowchart LR;
    Start([Fox or Hound]);
    Clear([Clear]);
    Start --> Subscribed0{Subscribed?};
    Subscribed0 -->|Yes| Heartbeat0{Heartbeat<br>alive?};
    Heartbeat0 -->|Yes| Rig0{Rig status?};
    Heartbeat0 -->|No| Subscribed0;
    Subscribed0 -->|No| Subscribed1[Subscribe];
    Subscribed1 --> Sleep0[Sleep];
    Sleep0 -->|Retry| Subscribed0;
    Rig0 -->|Yes| Rig1(Request rig status);
    Rig1 --> QSO0{QSO?};
    Rig0 -->|No| QSO0; 
    QSO0 -->|Yes| Lookup0{Lookup?};
    QSO0 -->|No| Heartbeat0;
    Lookup0 -->|Yes| Lookup1(Request Query Log);
    Lookup1 --> LogQSO0;
    Lookup0 -->|No| LogQSO0{Log?};
    LogQSO0 -->|Yes| LogQSO1(Publish Log QSO);
    LogQSO1 --> Clear;
    LogQSO0 -->|No| Clear;
    Clear -->|Loop| Start;
```

---

### Rig status request

```mermaid
flowchart LR;
    Start([Rig status]);
    Start --> Subscribed0{Subscribed?};
    Subscribed0 -->|Yes| Request0{Request?};
    Subscribed0 -->|No| Subscribed1[Subscribe];
    Subscribed1 --> Sleep0[Sleep];
    Request0 -->|Yes| Read0[rigctld read];
    Sleep0 -->|Retry| Subscribed0;
    Request0 -->|No| Heartbeat0(Heartbeat);
    Heartbeat0 -->|Loop| Subscribed0;
    Read0 --> Read1{Success?};
    Read1 -->|Yes| Publish0[Publish rig status];
    Read1 -->|No| Read0;
    Publish0 -->|Loop| Start;    
```

---

### Log QSO request

```mermaid
flowchart LR;
    LogQSO([Log QSO]);
    LogQSO --> Subscribed0{Subscribed?};
    Subscribed0 -->|Yes| Request0{Request?};
    Subscribed0 -->|No| Subscribed1[Subscribe];
    Subscribed1 --> Sleep0[Sleep];
    Sleep0 -->|Retry| Subscribed0;
    Request0 -->|Yes| WriteQSO0[Write QSO];
    Request0 -->|No| Heartbeat0(Heartbeat);
    Heartbeat0 -->|Loop| Subscribed0;
    WriteQSO0 --> Publish0[Publish Log QSO];
    Publish0 -->|Loop| Subscribed0;
```

---

### Query Log request

```mermaid
flowchart LR;
    QueryQSO([Query QSO]);
    QueryQSO --> Subscribed0{Subscribed?};
    Subscribed0 -->|Yes| Request0{Request?};
    Subscribed0 -->|No| Subscribed1[Subscribe];
    Subscribed1 --> Sleep0[Sleep];
    Sleep0 -->|Retry| Subscribed0;
    Request0 -->|Yes| ReadQSO0[Read QSO];
    Request0 -->|No| Heartbeat(Heartbeat);
    Heartbeat -->|Loop| Subscribed0;
    ReadQSO0 --> Publish0[Publish Read QSO];
    Publish0 -->|Loop| Subscribed0;    
```

---

### Publish heartbeat

```mermaid
flowchart LR;
    Heartbeat([Heartbeat]);
    Heartbeat --> Subscribed0{Subscribed?};
    Subscribed0 -->|No| Subscribed1[Subscribe];
    Subscribed1 --> Sleep0[Sleep];
    Sleep0 -->|Retry| Subscribed0;
    Subscribed0 -->|Yes| Wait0[wait];
    Wait0 --> Publish0[Publish heartbeat for process];
    Publish0 -->|Loop| Subscribed0;
    
```
