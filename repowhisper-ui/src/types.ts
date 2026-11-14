export interface FileAnalysis {
    file: string;
    code_snippet: string;
    explanation: string;
    notes?: Record<number, string>;
}

export interface RepoData {
    title: string;
    narrative: string;
    tree_structure: string;
    raw_modules: FileAnalysis[];
    files?: Record<string, FileAnalysis>;
}

export interface ModuleData {
    path: string;
    title: string;
    explanation: string;
    code_snippet?: string;
    notes?: Record<number, string>;
}
