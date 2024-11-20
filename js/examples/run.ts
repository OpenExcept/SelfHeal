import { config } from 'dotenv';
import * as path from 'path';

// Load environment variables from .env file
config({ path: path.join(__dirname, '../.env') });

// Import and run the data processor example
import './DataProcessor'; 