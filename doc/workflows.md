# Ham workflows

Different microservice flows broken down with interactions.  Each workflow publishes a heartbeat when not performing work and after work is successfully completed.  The heartbeat wait interval must be _greater_ than the slowest operation to prevent the heartbeat from going stale.

1. [Fox or Hound](#fox-or-hound)  
    Calls _Rig status request_, _Query Log reqeust_, _Log QSO request_, and _Publish Heartbeat_

2. [Rig status request](#rig-status-request)  
    Calls _Publish Heartbeat_

3. [Log QSO request](#log-qso-request)  
    Calls _Publish Heartbeat_

4. [Query Log request](#query-log-request)  
    Calls _Publish Heartbeat_

5. [Publish Heartbeat](#publish-heartbeat)



## Workflows

### Fox or Hound

```mermaid
flowchart LR;
    Start([Fox or Hound]);
    Clear([Clear]);
    Start --> Subscribed0{Subscribed?};
    Subscribed0 -->|No| Subscribed1[Subscribe];
    Subscribed1 --> Sleep0[Sleep];
    Sleep0 -->|Retry| Subscribed0;
    Wait0 -->|Retry| Subscribed0;    Rig0 -->|Yes| Rig1(Request rig status);
    Subscribed0 -->|Yes| Health0{Healthy?};
    Health0 -->|Yes| Rig0{Rig status?};
    Health0 -->|No| Warn0[Warn op];
    Warn0 --> Wait0[Wait];
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

---

### Service health

```mermaid
flowchart LR;
    Health([Service status])
    Health --> Subscribed0{Subscribed?};
    Subscribed0 -->|No| Subscribed1[Subscribe];
    Subscribed1 --> Sleep0[Sleep];
    Sleep0 -->|Retry| Subscribed0;
    Subscribed0 -->|Yes| Heartbeat0{Heartbeat?};
    Heartbeat0 -->|Yes| Zero0[Zero service timer];
    Zero0 -->|Check for more heartbeats| Heartbeat0;
    Heartbeat0 -->|No| Watermark0[Record highest service timer];
    Watermark0 --> Watermark1{High<br>watermark<br> reached?};
    Watermark1 --> |No| Alive0[Mark alive];
    Alive0 --> Publish0;
    Watermark1 --> |Yes| Dead0[Mark dead];
    Dead0 --> Publish0[Publish overall and<br>per service health];
    Publish0 --> Wait0[Wait];
    Wait0 -->|Loop| Subscribed0;
```