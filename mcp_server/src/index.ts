#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";
import fs from 'fs-extra';
import path from 'path';
import { glob } from 'glob';
import mysql from 'mysql2/promise';
import { createReadStream, createWriteStream } from 'fs';
import csv from 'csv-parser';
import archiver from 'archiver';
import { Extract } from 'unzipper';
import { spawn } from 'child_process';
import { promisify } from 'util';

// Project root - adjust this path to your CRM project location
const PROJECT_ROOT = '/Users/ahmedgomaa/Downloads/crm';

// MariaDB connection configuration
const DB_CONFIG = {
  host: 'localhost',
  user: 'root',
  password: 'your_password_here', // Update this with your actual password
  database: 'django_db_glomart_rs',
  port: 3306
};

class GlomartCRMServer {
  private server: Server;
  private dbConnection: mysql.Connection | null = null;

  constructor() {
    this.server = new Server(
      {
        name: "glomart-crm-mcp-server",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    
    // Error handling
    this.server.onerror = (error) => console.error("[MCP Error]", error);
    process.on("SIGINT", async () => {
      await this.cleanup();
      process.exit(0);
    });
  }

  private async cleanup() {
    if (this.dbConnection) {
      await this.dbConnection.end();
    }
  }

  private async connectToDatabase() {
    try {
      if (!this.dbConnection) {
        this.dbConnection = await mysql.createConnection(DB_CONFIG);
        console.log('Connected to MariaDB');
      }
      return this.dbConnection;
    } catch (error) {
      throw new McpError(ErrorCode.InternalError, `Database connection failed: ${error}`);
    }
  }

  private setupToolHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        // File System Tools
        {
          name: "read_file",
          description: "Read contents of a file in the CRM project",
          inputSchema: {
            type: "object",
            properties: {
              path: { type: "string", description: "File path relative to project root" },
              encoding: { type: "string", description: "File encoding (default: utf8)" }
            },
            required: ["path"]
          }
        },
        {
          name: "write_file",
          description: "Write content to a file in the CRM project",
          inputSchema: {
            type: "object",
            properties: {
              path: { type: "string", description: "File path relative to project root" },
              content: { type: "string", description: "Content to write" },
              encoding: { type: "string", description: "File encoding (default: utf8)" }
            },
            required: ["path", "content"]
          }
        },
        {
          name: "list_files",
          description: "List files in a directory with optional glob pattern",
          inputSchema: {
            type: "object",
            properties: {
              path: { type: "string", description: "Directory path relative to project root (default: '')" },
              pattern: { type: "string", description: "Glob pattern to filter files (default: '**/*')" },
              include_hidden: { type: "boolean", description: "Include hidden files (default: false)" }
            }
          }
        },
        {
          name: "search_files",
          description: "Search for text content in files",
          inputSchema: {
            type: "object",
            properties: {
              query: { type: "string", description: "Text to search for" },
              path: { type: "string", description: "Directory to search in (default: project root)" },
              file_pattern: { type: "string", description: "File pattern to search in (default: '**/*.py')" },
              case_sensitive: { type: "boolean", description: "Case sensitive search (default: false)" }
            },
            required: ["query"]
          }
        },
        {
          name: "create_directory",
          description: "Create a directory in the project",
          inputSchema: {
            type: "object",
            properties: {
              path: { type: "string", description: "Directory path relative to project root" }
            },
            required: ["path"]
          }
        },
        {
          name: "delete_file",
          description: "Delete a file or directory",
          inputSchema: {
            type: "object",
            properties: {
              path: { type: "string", description: "File/directory path relative to project root" },
              recursive: { type: "boolean", description: "Delete recursively for directories (default: false)" }
            },
            required: ["path"]
          }
        },
        
        // Database Tools
        {
          name: "execute_sql",
          description: "Execute a SQL query on the MariaDB database",
          inputSchema: {
            type: "object",
            properties: {
              query: { type: "string", description: "SQL query to execute" },
              params: { type: "array", description: "Query parameters" }
            },
            required: ["query"]
          }
        },
        {
          name: "list_tables",
          description: "List all tables in the database",
          inputSchema: {
            type: "object",
            properties: {
              database: { type: "string", description: "Database name (optional)" }
            }
          }
        },
        {
          name: "describe_table",
          description: "Get table structure and column information",
          inputSchema: {
            type: "object",
            properties: {
              table: { type: "string", description: "Table name" }
            },
            required: ["table"]
          }
        },
        {
          name: "backup_database",
          description: "Create a database backup",
          inputSchema: {
            type: "object",
            properties: {
              output_file: { type: "string", description: "Backup file path (optional)" }
            }
          }
        },

        // Django Tools
        {
          name: "django_manage",
          description: "Run Django management commands",
          inputSchema: {
            type: "object",
            properties: {
              command: { type: "string", description: "Django management command (e.g., 'migrate', 'collectstatic')" },
              args: { type: "array", description: "Command arguments" }
            },
            required: ["command"]
          }
        },
        {
          name: "django_shell",
          description: "Execute Python code in Django shell context",
          inputSchema: {
            type: "object",
            properties: {
              code: { type: "string", description: "Python code to execute" }
            },
            required: ["code"]
          }
        },

        // Git Tools
        {
          name: "git_status",
          description: "Get git repository status",
          inputSchema: { type: "object", properties: {} }
        },
        {
          name: "git_commit",
          description: "Commit changes to git",
          inputSchema: {
            type: "object",
            properties: {
              message: { type: "string", description: "Commit message" },
              add_all: { type: "boolean", description: "Add all changes before commit (default: false)" }
            },
            required: ["message"]
          }
        },
        {
          name: "git_push",
          description: "Push changes to remote repository",
          inputSchema: {
            type: "object",
            properties: {
              remote: { type: "string", description: "Remote name (default: origin)" },
              branch: { type: "string", description: "Branch name (default: main)" }
            }
          }
        },

        // Project Analysis Tools
        {
          name: "analyze_models",
          description: "Analyze Django models in the project",
          inputSchema: {
            type: "object",
            properties: {
              app: { type: "string", description: "Specific app to analyze (optional)" }
            }
          }
        },
        {
          name: "project_stats",
          description: "Get project statistics (files, lines of code, etc.)",
          inputSchema: { type: "object", properties: {} }
        }
      ]
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case "read_file":
            return await this.readFile(args.path, args.encoding);
          case "write_file":
            return await this.writeFile(args.path, args.content, args.encoding);
          case "list_files":
            return await this.listFiles(args.path, args.pattern, args.include_hidden);
          case "search_files":
            return await this.searchFiles(args.query, args.path, args.file_pattern, args.case_sensitive);
          case "create_directory":
            return await this.createDirectory(args.path);
          case "delete_file":
            return await this.deleteFile(args.path, args.recursive);
          case "execute_sql":
            return await this.executeSql(args.query, args.params);
          case "list_tables":
            return await this.listTables(args.database);
          case "describe_table":
            return await this.describeTable(args.table);
          case "backup_database":
            return await this.backupDatabase(args.output_file);
          case "django_manage":
            return await this.djangoManage(args.command, args.args);
          case "django_shell":
            return await this.djangoShell(args.code);
          case "git_status":
            return await this.gitStatus();
          case "git_commit":
            return await this.gitCommit(args.message, args.add_all);
          case "git_push":
            return await this.gitPush(args.remote, args.branch);
          case "analyze_models":
            return await this.analyzeModels(args.app);
          case "project_stats":
            return await this.projectStats();
          default:
            throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
        }
      } catch (error) {
        throw new McpError(ErrorCode.InternalError, `Tool execution failed: ${error}`);
      }
    });
  }

  // File System Operations
  private async readFile(filePath: string, encoding: string = 'utf8') {
    const fullPath = path.join(PROJECT_ROOT, filePath);
    const content = await fs.readFile(fullPath, encoding);
    return {
      content: [
        {
          type: "text",
          text: `File: ${filePath}\n\n${content}`
        }
      ]
    };
  }

  private async writeFile(filePath: string, content: string, encoding: string = 'utf8') {
    const fullPath = path.join(PROJECT_ROOT, filePath);
    await fs.ensureDir(path.dirname(fullPath));
    await fs.writeFile(fullPath, content, encoding);
    return {
      content: [
        {
          type: "text",
          text: `File written successfully: ${filePath}`
        }
      ]
    };
  }

  private async listFiles(dirPath: string = '', pattern: string = '**/*', includeHidden: boolean = false) {
    const fullPath = path.join(PROJECT_ROOT, dirPath);
    const globPattern = path.join(fullPath, pattern);
    const files = await glob(globPattern, { 
      dot: includeHidden,
      nodir: false 
    });
    
    const relativePaths = files.map(file => path.relative(PROJECT_ROOT, file));
    
    return {
      content: [
        {
          type: "text",
          text: `Files in ${dirPath || 'project root'}:\n\n${relativePaths.join('\n')}`
        }
      ]
    };
  }

  private async searchFiles(query: string, searchPath: string = '', filePattern: string = '**/*.py', caseSensitive: boolean = false) {
    const fullPath = path.join(PROJECT_ROOT, searchPath);
    const globPattern = path.join(fullPath, filePattern);
    const files = await glob(globPattern);
    
    const results: string[] = [];
    const searchFlags = caseSensitive ? 'g' : 'gi';
    const regex = new RegExp(query, searchFlags);

    for (const file of files) {
      const content = await fs.readFile(file, 'utf8');
      const lines = content.split('\n');
      
      lines.forEach((line, index) => {
        if (regex.test(line)) {
          const relativePath = path.relative(PROJECT_ROOT, file);
          results.push(`${relativePath}:${index + 1}: ${line.trim()}`);
        }
      });
    }

    return {
      content: [
        {
          type: "text",
          text: `Search results for "${query}":\n\n${results.join('\n')}`
        }
      ]
    };
  }

  private async createDirectory(dirPath: string) {
    const fullPath = path.join(PROJECT_ROOT, dirPath);
    await fs.ensureDir(fullPath);
    return {
      content: [
        {
          type: "text",
          text: `Directory created: ${dirPath}`
        }
      ]
    };
  }

  private async deleteFile(filePath: string, recursive: boolean = false) {
    const fullPath = path.join(PROJECT_ROOT, filePath);
    if (recursive) {
      await fs.remove(fullPath);
    } else {
      await fs.unlink(fullPath);
    }
    return {
      content: [
        {
          type: "text",
          text: `Deleted: ${filePath}`
        }
      ]
    };
  }

  // Database Operations
  private async executeSql(query: string, params: any[] = []) {
    const db = await this.connectToDatabase();
    const [rows, fields] = await db.execute(query, params);
    
    return {
      content: [
        {
          type: "text",
          text: `SQL Query Result:\n\n${JSON.stringify(rows, null, 2)}`
        }
      ]
    };
  }

  private async listTables(database?: string) {
    const db = await this.connectToDatabase();
    const query = database ? 
      `SELECT table_name FROM information_schema.tables WHERE table_schema = ?` :
      `SHOW TABLES`;
    const params = database ? [database] : [];
    const [rows] = await db.execute(query, params);
    
    return {
      content: [
        {
          type: "text",
          text: `Database Tables:\n\n${JSON.stringify(rows, null, 2)}`
        }
      ]
    };
  }

  private async describeTable(table: string) {
    const db = await this.connectToDatabase();
    const [rows] = await db.execute(`DESCRIBE ${table}`);
    
    return {
      content: [
        {
          type: "text",
          text: `Table Structure for ${table}:\n\n${JSON.stringify(rows, null, 2)}`
        }
      ]
    };
  }

  private async backupDatabase(outputFile?: string) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupFile = outputFile || `backup-${timestamp}.sql`;
    
    // Use mysqldump command
    const command = `mysqldump -h ${DB_CONFIG.host} -u ${DB_CONFIG.user} -p${DB_CONFIG.password} ${DB_CONFIG.database}`;
    
    return new Promise((resolve, reject) => {
      const child = spawn('mysqldump', [
        `-h${DB_CONFIG.host}`,
        `-u${DB_CONFIG.user}`,
        `-p${DB_CONFIG.password}`,
        DB_CONFIG.database
      ]);

      const backupPath = path.join(PROJECT_ROOT, backupFile);
      const output = fs.createWriteStream(backupPath);
      
      child.stdout.pipe(output);
      
      child.on('close', (code) => {
        if (code === 0) {
          resolve({
            content: [
              {
                type: "text",
                text: `Database backup created: ${backupFile}`
              }
            ]
          });
        } else {
          reject(new Error(`mysqldump failed with code ${code}`));
        }
      });
    });
  }

  // Django Operations
  private async djangoManage(command: string, args: string[] = []) {
    return new Promise((resolve, reject) => {
      const child = spawn('python', ['manage.py', command, ...args], {
        cwd: PROJECT_ROOT,
        stdio: 'pipe'
      });

      let output = '';
      let errorOutput = '';

      child.stdout.on('data', (data) => {
        output += data.toString();
      });

      child.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });

      child.on('close', (code) => {
        const result = output + (errorOutput ? `\nErrors:\n${errorOutput}` : '');
        resolve({
          content: [
            {
              type: "text",
              text: `Django Command: python manage.py ${command} ${args.join(' ')}\n\n${result}`
            }
          ]
        });
      });
    });
  }

  private async djangoShell(code: string) {
    const tempScript = `
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
django.setup()

${code}
`;

    return new Promise((resolve, reject) => {
      const child = spawn('python', ['-c', tempScript], {
        cwd: PROJECT_ROOT,
        stdio: 'pipe'
      });

      let output = '';
      let errorOutput = '';

      child.stdout.on('data', (data) => {
        output += data.toString();
      });

      child.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });

      child.on('close', (code) => {
        const result = output + (errorOutput ? `\nErrors:\n${errorOutput}` : '');
        resolve({
          content: [
            {
              type: "text",
              text: `Django Shell Execution:\n\n${result}`
            }
          ]
        });
      });
    });
  }

  // Git Operations
  private async gitStatus() {
    return new Promise((resolve, reject) => {
      const child = spawn('git', ['status', '--porcelain'], {
        cwd: PROJECT_ROOT,
        stdio: 'pipe'
      });

      let output = '';
      child.stdout.on('data', (data) => {
        output += data.toString();
      });

      child.on('close', (code) => {
        resolve({
          content: [
            {
              type: "text",
              text: `Git Status:\n\n${output || 'Working directory clean'}`
            }
          ]
        });
      });
    });
  }

  private async gitCommit(message: string, addAll: boolean = false) {
    const commands = addAll ? [['add', '.'], ['commit', '-m', message]] : [['commit', '-m', message]];
    
    let output = '';
    
    for (const command of commands) {
      const result = await new Promise<string>((resolve, reject) => {
        const child = spawn('git', command, {
          cwd: PROJECT_ROOT,
          stdio: 'pipe'
        });

        let commandOutput = '';
        child.stdout.on('data', (data) => {
          commandOutput += data.toString();
        });

        child.stderr.on('data', (data) => {
          commandOutput += data.toString();
        });

        child.on('close', (code) => {
          resolve(commandOutput);
        });
      });
      
      output += `git ${command.join(' ')}:\n${result}\n\n`;
    }

    return {
      content: [
        {
          type: "text",
          text: output
        }
      ]
    };
  }

  private async gitPush(remote: string = 'origin', branch: string = 'main') {
    return new Promise((resolve, reject) => {
      const child = spawn('git', ['push', remote, branch], {
        cwd: PROJECT_ROOT,
        stdio: 'pipe'
      });

      let output = '';
      let errorOutput = '';

      child.stdout.on('data', (data) => {
        output += data.toString();
      });

      child.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });

      child.on('close', (code) => {
        const result = output + errorOutput;
        resolve({
          content: [
            {
              type: "text",
              text: `Git Push Result:\n\n${result}`
            }
          ]
        });
      });
    });
  }

  // Project Analysis
  private async analyzeModels(app?: string) {
    const pattern = app ? `${app}/models.py` : '**/models.py';
    const modelFiles = await glob(path.join(PROJECT_ROOT, pattern));
    
    let analysis = 'Django Models Analysis:\n\n';
    
    for (const file of modelFiles) {
      const content = await fs.readFile(file, 'utf8');
      const relativePath = path.relative(PROJECT_ROOT, file);
      
      // Simple model class extraction
      const modelMatches = content.match(/class\s+(\w+)\s*\([^)]*Model[^)]*\):/g);
      
      analysis += `File: ${relativePath}\n`;
      if (modelMatches) {
        modelMatches.forEach(match => {
          const modelName = match.match(/class\s+(\w+)/)?.[1];
          analysis += `  - ${modelName}\n`;
        });
      }
      analysis += '\n';
    }

    return {
      content: [
        {
          type: "text",
          text: analysis
        }
      ]
    };
  }

  private async projectStats() {
    const files = await glob(path.join(PROJECT_ROOT, '**/*'), { nodir: true });
    
    const stats = {
      totalFiles: files.length,
      pythonFiles: 0,
      htmlFiles: 0,
      cssFiles: 0,
      jsFiles: 0,
      totalLines: 0
    };

    for (const file of files) {
      const ext = path.extname(file).toLowerCase();
      
      if (ext === '.py') stats.pythonFiles++;
      else if (ext === '.html') stats.htmlFiles++;
      else if (ext === '.css') stats.cssFiles++;
      else if (ext === '.js') stats.jsFiles++;
      
      try {
        const content = await fs.readFile(file, 'utf8');
        stats.totalLines += content.split('\n').length;
      } catch (error) {
        // Skip binary files
      }
    }

    return {
      content: [
        {
          type: "text",
          text: `Project Statistics:\n\n${JSON.stringify(stats, null, 2)}`
        }
      ]
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Glomart CRM MCP server running on stdio");
  }
}

const server = new GlomartCRMServer();
server.run().catch(console.error);