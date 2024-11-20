import { FunctionDebugger } from '../index';
import { randomUUID } from 'crypto';

// Initialize debugger with Slack integration
const SLACK_TOKEN = process.env.SLACK_BOT_TOKEN;
if (!SLACK_TOKEN) {
    console.warn("⚠️  Warning: SLACK_BOT_TOKEN not set in environment");
}

const debugInstance = new FunctionDebugger({
    dumpDir: "/root/debug_states",
    useS3: false,
    slackToken: SLACK_TOKEN
});

interface DataRecord {
    id: string;
    timestamp: Date;
    values: number[];
    metadata: {
        source: string;
        quality: 'high' | 'medium' | 'low';
        processed?: boolean;
        config?: any;
    };
}

class DataNormalizer {
    constructor(private scalingFactor: number = 1.0) {}
    
    normalizeValues(values: number[]): number[] {
        return values.map(v => v * this.scalingFactor);
    }
}

@debugInstance.debugEnabled()
class DataProcessor {
    private normalizer: DataNormalizer;
    private processedRecords: DataRecord[] = [];

    constructor(private batchSize: number = 10) {
        this.normalizer = new DataNormalizer(1.5);
    }

    private generateSampleData(): DataRecord[] {
        const records: DataRecord[] = [];
        
        for (let i = 0; i < this.batchSize; i++) {
            const record: DataRecord = {
                id: `REC_${randomUUID()}`,
                timestamp: new Date(),
                values: Array(3).fill(0).map(() => Math.random() * 100),
                metadata: {
                    source: `sensor_${Math.floor(Math.random() * 5) + 1}`,
                    quality: ['high', 'medium', 'low'][Math.floor(Math.random() * 3)] as 'high' | 'medium' | 'low'
                }
            };
            records.push(record);
        }
        
        return records;
    }

    @debugInstance.debugEnabled()
    private validateRecord(record: DataRecord): boolean {
        if (record.values.length === 0) {
            return false;
        }

        if (record.values.some(v => v < 0)) {
            return false;
        }

        if (record.metadata.quality === 'low') {
            return false;
        }

        return true;
    }

    @debugInstance.debugEnabled()
    private processRecord(record: DataRecord): DataRecord {
        // This will cause an unexpected exception when processing certain records
        if (record.metadata.source === 'sensor_3') {
            // Simulate a deep attribute access that fails
            try {
                // This will raise a TypeError
                const config = record.metadata.config?.normalization?.type;
                if (!config) {
                    throw new Error(`Missing configuration for ${record.id}`);
                }
            } catch (error) {
                throw new Error(`Missing configuration for ${record.id}`);
            }
        }

        const normalizedValues = this.normalizer.normalizeValues(record.values);

        return {
            ...record,
            values: normalizedValues,
            metadata: {
                ...record.metadata,
                processed: true
            }
        };
    }

    @debugInstance.debugEnabled()
    async processBatch(): Promise<DataRecord[]> {
        const records = this.generateSampleData();
        const processedRecords: DataRecord[] = [];

        for (const record of records) {
            if (this.validateRecord(record)) {
                const processedRecord = this.processRecord(record);
                processedRecords.push(processedRecord);
            } else {
                console.log(`Skipping invalid record: ${record.id}`);
            }
        }

        this.processedRecords.push(...processedRecords);
        return processedRecords;
    }
}

async function main() {
    // Initialize processor
    const processor = new DataProcessor(5);

    // Process multiple batches
    try {
        for (let i = 0; i < 3; i++) {
            console.log(`\nProcessing batch ${i + 1}...`);
            const processed = await processor.processBatch();
            console.log(`Successfully processed ${processed.length} records`);
        }
    } catch (error: any) {
        console.log(`\n❌ Error during processing: ${error.message}`);
        if ('debugDumpPath' in error) {
            console.log(`Debug state dumped to: ${error.debugDumpPath}`);
        }
        if ('slackThreadTs' in error) {
            console.log(`Slack thread timestamp: ${error.slackThreadTs}`);
        }
        throw error;
    }
}

// Run the example
if (require.main === module) {
    main().catch(console.error);
} 