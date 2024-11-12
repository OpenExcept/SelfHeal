import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime
import random

from selfheal import FunctionDebugger

# Initialize debugger with Slack integration
SLACK_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
if not SLACK_TOKEN:
    print("⚠️  Warning: SLACK_BOT_TOKEN not set in environment")

debugger = FunctionDebugger(
    dump_dir="/root/debug_states",
    use_s3=False,
    slack_token=SLACK_TOKEN
)

@dataclass
class DataRecord:
    id: str
    timestamp: datetime
    values: List[float]
    metadata: Dict[str, Any]

class DataNormalizer:
    def __init__(self, scaling_factor: float = 1.0):
        self.scaling_factor = scaling_factor
        self._processed_count = 0
        
    def normalize_values(self, values: List[float]) -> List[float]:
        return [v * self.scaling_factor for v in values]

@debugger.debug_class()
class DataProcessor:
    def __init__(self, batch_size: int = 10):
        self.batch_size = batch_size
        self.normalizer = DataNormalizer(scaling_factor=1.5)
        self.processed_records = []
        
    def generate_sample_data(self) -> List[DataRecord]:
        """Generate sample data records with some random values."""
        records = []
        for i in range(self.batch_size):
            record = DataRecord(
                id=f"REC_{i}",
                timestamp=datetime.now(),
                values=[random.uniform(0, 100) for _ in range(3)],
                metadata={
                    "source": "sensor_" + str(random.randint(1, 5)),
                    "quality": random.choice(["high", "medium", "low"])
                }
            )
            records.append(record)
        return records
    
    def validate_record(self, record: DataRecord) -> bool:
        """Validate a single data record."""
        if not record.values:
            return False
        
        if any(v < 0 for v in record.values):
            return False
            
        if record.metadata.get("quality") == "low":
            return False
            
        return True
    
    def process_record(self, record: DataRecord) -> DataRecord:
        """Process a single record with normalization."""
        # This will cause an unexpected exception when processing certain records
        if record.metadata["source"] == "sensor_3":
            # Simulate a deep attribute access that fails
            try:
                # This will raise an AttributeError
                record.metadata["config"]["normalization"]["type"]
            except KeyError as e:
                raise AttributeError(f"Missing configuration for {record.id}") from e
        
        normalized_values = self.normalizer.normalize_values(record.values)
        
        # Create new record with normalized values
        return DataRecord(
            id=record.id,
            timestamp=record.timestamp,
            values=normalized_values,
            metadata={**record.metadata, "processed": True}
        )
    
    def process_batch(self) -> List[DataRecord]:
        """Process a batch of records."""
        records = self.generate_sample_data()
        processed_records = []
        
        for record in records:
            if self.validate_record(record):
                processed_record = self.process_record(record)
                processed_records.append(processed_record)
            else:
                print(f"Skipping invalid record: {record.id}")
        
        self.processed_records.extend(processed_records)
        return processed_records

def main():
    # Initialize processor
    processor = DataProcessor(batch_size=5)
    
    # Process multiple batches
    try:
        for i in range(3):
            print(f"\nProcessing batch {i+1}...")
            processed = processor.process_batch()
            print(f"Successfully processed {len(processed)} records")
            
    except Exception as e:
        print(f"\n❌ Error during processing: {str(e)}")
        if hasattr(e, 'debug_dump_path'):
            print(f"Debug state dumped to: {e.debug_dump_path}")
        if hasattr(e, 'slack_thread_ts'):
            print(f"Slack thread timestamp: {e.slack_thread_ts}")
        raise

if __name__ == "__main__":
    main() 