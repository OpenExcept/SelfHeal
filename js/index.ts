import { mkdir, writeFile } from 'fs/promises';
import { join } from 'path';
import { DebugState, FunctionDebuggerOptions, StackFrame } from './types';
import { S3Storage } from './S3Storage';
import { SlackAlert } from './SlackAlert';
import { readFileSync } from 'fs';
import { SourceMapConsumer } from 'source-map';
import * as path from 'path';
import { parseScript } from 'esprima';
import { traverse } from 'estraverse';

export class FunctionDebugger {
  private dumpDir: string;
  private useS3: boolean;
  private s3Storage?: S3Storage;
  private slackAlert?: SlackAlert;
  private s3Bucket: string = 'debug-state-dumps';

  constructor(options: FunctionDebuggerOptions = {}) {
    this.dumpDir = options.dumpDir || './debug_states';
    this.useS3 = options.useS3 || false;
    
    if (this.useS3) {
      this.s3Storage = new S3Storage();
    }

    if (options.slackToken) {
      this.slackAlert = new SlackAlert(options.slackToken);
    }

    // Ensure dump directory exists
    mkdir(this.dumpDir, { recursive: true }).catch(console.error);
  }

  private async getStackFrames(error: Error): Promise<StackFrame[]> {
    const frames: StackFrame[] = [];
    
    if (!error.stack) return frames;

    const stackLines = error.stack.split('\n').slice(1);
    for (const line of stackLines) {
      const match = line.match(/at (?:(.+?)\s+\()?(?:(.+?):(\d+):(\d+))/);
      if (match) {
        const [, functionName, fileName, lineStr, columnStr] = match;
        const lineNumber = parseInt(lineStr, 10);
        
        try {
          const localVars = await this.getLocalVars();
          const functionCode = await this.getFunctionCode(fileName, lineNumber);
          
          frames.push({
            fileName: fileName || 'unknown',
            functionName: functionName || 'anonymous',
            lineNumber: lineNumber,
            columnNumber: parseInt(columnStr, 10),
            localVars,
            functionCode
          });
        } catch (e) {
          console.warn('Failed to capture frame info:', e);
        }
      }
    }

    return frames;
  }

  private async getLocalVars(): Promise<Record<string, string>> {
    try {
      // Get the current stack trace
      const stack = new Error().stack;
      if (!stack) return {};

      // Get the caller's frame (skip first two frames - Error and getLocalVars)
      const frames = stack.split('\n').slice(2);
      const callerFrame = frames[0];

      // Extract file and line information
      const match = callerFrame.match(/at (?:(.+?)\s+\()?(?:(.+?):(\d+):(\d+))/);
      if (!match) return {};

      const [, , fileName, lineNumber] = match;

      // Read the source file
      const sourceCode = readFileSync(fileName, 'utf-8');

      // Parse the source code to AST
      const ast = parseScript(sourceCode, { loc: true });
      
      const localVars: Record<string, string> = {};

      // Find variables declared in the scope of the error
      traverse(ast, {
        enter: (node: any) => {
          if (
            node.type === 'VariableDeclaration' && 
            node.loc && 
            node.loc.start.line <= parseInt(lineNumber, 10)
          ) {
            node.declarations.forEach((decl: any) => {
              if (decl.id.type === 'Identifier') {
                try {
                  // Attempt to get the runtime value using Error.captureStackTrace
                  const value = this.getCapturedVariable(decl.id.name);
                  localVars[decl.id.name] = value !== undefined ? String(value) : 'undefined';
                } catch (e) {
                  localVars[decl.id.name] = '<inaccessible>';
                }
              }
            });
          }
        }
      });

      return localVars;
    } catch (error) {
      console.warn('Failed to capture local variables:', error);
      return {};
    }
  }

  private async getFunctionCode(fileName: string, lineNumber: number): Promise<string> {
    try {
      // Check if we're dealing with a source map
      const sourceMapPath = fileName + '.map';
      let sourceCode: string;
      let actualFileName = fileName;
      let actualLineNumber = lineNumber;

      try {
        // Try to read source map if it exists
        const sourceMapContent = readFileSync(sourceMapPath, 'utf-8');
        const consumer = await new SourceMapConsumer(sourceMapContent);
        
        // Get original position
        const original = consumer.originalPositionFor({
          line: lineNumber,
          column: 0
        });

        if (original.source) {
          actualFileName = path.resolve(path.dirname(fileName), original.source);
          actualLineNumber = original.line || lineNumber;
        }

        consumer.destroy();
      } catch (e) {
        // No source map found, use the original file
      }

      // Read the source file
      sourceCode = readFileSync(actualFileName, 'utf-8');

      // Parse the source to find the function boundaries
      const ast = parseScript(sourceCode, { loc: true });
      let functionCode = '';
      let foundFunction = false;

      traverse(ast, {
        enter: (node: any) => {
          if (
            (node.type === 'FunctionDeclaration' || 
             node.type === 'FunctionExpression' ||
             node.type === 'ArrowFunctionExpression') &&
            node.loc &&
            node.loc.start.line <= actualLineNumber &&
            node.loc.end.line >= actualLineNumber
          ) {
            // Extract the function code
            const lines = sourceCode.split('\n');
            functionCode = lines
              .slice(node.loc.start.line - 1, node.loc.end.line)
              .join('\n');
            foundFunction = true;
          }
        }
      });

      if (!foundFunction) {
        // If we couldn't find the function boundaries, return context around the error
        const lines = sourceCode.split('\n');
        const start = Math.max(0, actualLineNumber - 3);
        const end = Math.min(lines.length, actualLineNumber + 2);
        functionCode = lines.slice(start, end).join('\n');
      }

      return functionCode;
    } catch (error) {
      console.warn('Failed to get function code:', error);
      return 'Source code not available';
    }
  }

  private getCapturedVariable(varName: string): any {
    // This is a best-effort attempt to capture variable values
    // It won't work for all cases due to JS scope limitations
    const captureObject: Record<string, any> = {};
    Error.captureStackTrace(captureObject);
    
    return (captureObject as any)[varName];
  }

  private generateDumpPath(functionName: string): string {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    return join(this.dumpDir, `${functionName}_${timestamp}.json`);
  }

  private async dumpState(dumpPath: string, debugState: DebugState): Promise<string | null> {
    try {
      await writeFile(dumpPath, JSON.stringify(debugState, null, 2));
      console.log(`Saved debug dump to: ${dumpPath}`);

      if (this.useS3 && this.s3Storage) {
        const s3Key = dumpPath.split('/').pop()!;
        const success = await this.s3Storage.putObject(
          this.s3Bucket,
          dumpPath,
          s3Key
        );

        if (success) {
          const s3Uri = `s3://${this.s3Bucket}/${s3Key}`;
          console.log(`Uploaded debug dump to S3: ${s3Uri}`);
          return s3Uri;
        }
      }

      return dumpPath;
    } catch (error) {
      console.error('Failed to save debug dump:', error);
      return null;
    }
  }

  debugEnabled(dumpOnException: boolean = true) {
    const debuggerInstance = this;  // Capture the debugger instance
    
    return (target: any, propertyKey?: string, descriptor?: PropertyDescriptor) => {
      // If propertyKey is undefined, this is a class decorator
      if (!propertyKey) {
        // Return the class constructor unmodified
        return target;
      }

      // This is a method decorator
      if (!descriptor) return;
      
      const originalMethod = descriptor.value;

      descriptor.value = async function(...args: any[]) {
        try {
          return await originalMethod.apply(this, args);
        } catch (error) {
          if (dumpOnException && error instanceof Error) {
            const debugState: DebugState = {
              exception: {
                type: error.constructor.name,
                message: error.message,
                stack: error.stack || ''
              },
              isClassMethod: this !== undefined,
              stackFrames: await debuggerInstance.getStackFrames(error)
            };

            const dumpPath = debuggerInstance.generateDumpPath(propertyKey);
            const filePath = await debuggerInstance.dumpState(dumpPath, debugState);

            if (filePath && debuggerInstance.slackAlert) {
              await debuggerInstance.slackAlert.sendAlert({
                functionName: propertyKey,
                error,
                debugStatePath: filePath
              });
            }

            // Attach debug info to error
            (error as any).debugDumpPath = filePath;
          }
          throw error;
        }
      };

      return descriptor;
    };
  }
}

// Export decorator factory
export function debugEnabled(options: FunctionDebuggerOptions = {}) {
  const debugInstance = new FunctionDebugger(options);
  return debugInstance.debugEnabled();
} 