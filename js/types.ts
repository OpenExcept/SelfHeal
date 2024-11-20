export interface DebugState {
  exception: {
    type: string;
    message: string;
    stack: string;
  };
  isClassMethod: boolean;
  classInfo?: {
    className: string;
    moduleName: string;
    constructorArgs: Record<string, string>;
    constructorCode: string;
    classCode: string;
  };
  instanceState?: Record<string, any>;
  stackFrames: StackFrame[];
  filePath?: string;
}

export interface StackFrame {
  fileName: string;
  functionName: string;
  lineNumber: number;
  columnNumber: number;
  localVars: Record<string, string>;
  functionCode: string;
}

export interface FunctionDebuggerOptions {
  dumpDir?: string;
  useS3?: boolean;
  slackToken?: string;
}

export interface SourceLocation {
  line: number;
  column: number;
}

export interface SourcePosition {
  start: SourceLocation;
  end: SourceLocation;
}

export interface ASTNode {
  type: string;
  loc?: SourcePosition;
  [key: string]: any;
} 