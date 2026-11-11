export interface FileAnalysis {
    file: string,
    code_snippet: string;
    explanation: string;
}

export interface RepoData {
    title: string,
    narrative: string;
    tree_structure: string;
    files: Record<string, FileAnalysis>;
}