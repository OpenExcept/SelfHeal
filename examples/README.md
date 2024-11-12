# Selfheal Examples

This directory contains example applications that demonstrate the usage of the selfheal debugging framework.

## Data Processor Example

The `data_processor.py` example simulates a data processing pipeline with the following features:

- Processes batches of sensor data records
- Includes data validation and normalization
- Contains a hidden bug that triggers randomly
- Demonstrates class-level debugging
- Shows how debug states are captured and reported via Slack

### Running the Example

1. Set up your environment:
   ```bash
   export SLACK_BOT_TOKEN="your-slack-token"
   ```

2. Run the example:
   ```bash
   python examples/data_processor.py
   ```

### Expected Output

The example will:
1. Process multiple batches of records
2. Eventually encounter an error when processing data from "sensor_3"
3. Generate a debug state dump
4. Send a Slack alert with the error details
5. Add the debug state path as a thread reply

### Example Console Output

```
Processing batch 1...
Successfully processed 3 records

Processing batch 2...
Successfully processed 4 records

Processing batch 3...
❌ Error during processing: Missing configuration for REC_2
Debug state dumped to: /root/debug_states/process_record_20240320_123456.json
Slack thread timestamp: 1710901234.567890
Traceback (most recent call last):
  ...
AttributeError: Missing configuration for REC_2
```

### Example Slack Alert

The Slack alert will show:
```
🚨 Exception in function `process_record`
*Type:* `AttributeError`
*Message:* Missing configuration for REC_2
```

With a thread reply:
```
Debug state saved at: `/root/debug_states/process_record_20240320_123456.json`
```

### Debug State Contents

The generated debug state file will contain:
- Full exception details and traceback
- Class state of the DataProcessor
- State of the DataNormalizer
- The record that caused the failure
- Stack frames showing the execution path

This example demonstrates how selfheal captures detailed debugging information when exceptions occur, making it easier to diagnose and fix issues in production environments.