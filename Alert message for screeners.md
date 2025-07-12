# Alert Message Formats for TradingView Screeners

## Alert message for OB (Order Block) screener

### Single order block overlap:
```json
{
  "1": {
    "symbol": "EURUSD",
    "timeframe": "4 hours",
    "direction": "Buy",
    "screener": "OB",
    "timestamp": "1672531200", // UNIX timestamp of the bar which overlapped in an OB
    "info": {
      "obType": "bullish", // type of the OB which got overlapped in
      "obHigh": "1.0550", // top level of the OB
      "obLow": "1.0500", // bottom level of the OB
      "obTime": "1672520000", // the time where the OB originated
      "obPips": "5.0" // difference between top and bottom level of OB
    }
  }
}
```

### Multiple order block overlaps:
```json
{
  "1": {
    "symbol": "EURUSD",
    "timeframe": "4 hours",
    "direction": "Buy",
    "screener": "OB",
    "timestamp": "1672531200",
    "info": {
      "obType": "bullish",
      "obHigh": "1.0550",
      "obLow": "1.0500",
      "obTime": "1672520000",
      "obPips": "5.0"
    }
  },
  "2": {
    "symbol": "GBPUSD",
    "timeframe": "1 day",
    "direction": "Sell",
    "screener": "OB",
    "timestamp": "1672531200",
    "info": {
      "obType": "bearish",
      "obHigh": "1.2100",
      "obLow": "1.2050",
      "obTime": "1672520000",
      "obPips": "5.0"
    }
  }
}
```

## Alert message for NW (Nadaraya Watson) screener

### Single Nadaraya Watson signal:
```json
{
  "1": {
    "symbol": "EURUSD",
    "timeframe": "4 hours", 
    "direction": "Buy",
    "screener": "NW",
    "timestamp": "1672531200", // UNIX timestamp of the bar where the color change happened
    "info": {}
  }
}
```

### Multiple Nadaraya Watson signals:
```json
{
  "1": {
    "symbol": "EURUSD",
    "timeframe": "4 hours",
    "direction": "Buy",
    "screener": "NW",
    "timestamp": "1672531200",
    "info": {}
  },
  "2": {
    "symbol": "GBPUSD",
    "timeframe": "1 day",
    "direction": "Sell",
    "screener": "NW",
    "timestamp": "1672531200",
    "info": {}
  }
}
```

## Alert message for SB (Structure Break) screener

### Single structure break:
```json
{
  "1": {
    "symbol": "EURUSD",
    "timeframe": "4 hours",
    "direction": "Buy",
    "screener": "SB",
    "timestamp": "1672531200", // UNIX timestamp of the bar which broke the structure
    "info": {
      "zzDegree": "ZZ1", // ZigZag degree of the structure break
      "swing1": "1.0550", // Price of the oldest swing point
      "swing2": "1.0480", // Price of the 2nd oldest swing point
      "swing3": "1.0560", // Price of the 2nd latest swing point
      "swing4": "1.0560", // Price of the latest swing point
      "swing1Time": "1672520000", // UNIX timestamp of the oldest swing point
      "swing2Time": "1.0480", // UNIX timestamp of the 2nd oldest swing point
      "swing3Time": "1.0560", // UNIX timestamp of the 2nd latest swing point
      "swing4Time": "1.0560", // UNIX timestamp of the latest swing point
    }
  }
}
```

### Multiple structure breaks:
```json
{
  "1": {
    "symbol": "EURUSD",
    "timeframe": "4 hours",
    "direction": "Buy",
    "screener": "SB",
    "timestamp": "1672531200",
    "info": {
      "zzDegree": "ZZ1", 
      "swing1": "1.0550",
      "swing2": "1.0480",
      "swing3": "1.0560",
      "swing4": "1.0560",
      "swing1Time": "1672520000",
      "swing2Time": "1.0480",
      "swing3Time": "1.0560",
      "swing4Time": "1.0560",
    }
  },
  "2": {
    "symbol": "GBPUSD",
    "timeframe": "1 day",
    "direction": "Sell",
    "screener": "SB",
    "timestamp": "1672531200",
    "info": {
      "zzDegree": "ZZ1", 
      "swing1": "1.0550", 
      "swing2": "1.0480", 
      "swing3": "1.0560", 
      "swing4": "1.0560", 
      "swing1Time": "1672520000",
      "swing2Time": "1.0480", 
      "swing3Time": "1.0560", 
      "swing4Time": "1.0560",
    }
  }
}
```

### Structure Break Swing Point Logic:
- **Bullish Break (Buy)**: Price breaks ABOVE a high (resistance broken upward)
  - swing1 = broken high, swing2 = intermediate low, swing3 = current breaking price
- **Bearish Break (Sell)**: Price breaks BELOW a low (support broken downward)  
  - swing1 = broken low, swing2 = intermediate high, swing3 = current breaking price

### Structure Break Specific Features:
- **Contains detailed swing point data** for understanding the structure break pattern
- **Supports multiple breaks per symbol** (different ZigZag degrees) in same alert
- **ZigZag degree information** (ZZ1, ZZ2, ZZ3) indicating sensitivity level
