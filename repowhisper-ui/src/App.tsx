import { useState, useEffect } from 'react';
import { useRepoData } from './hooks/useRepoData';
import { motion, AnimatePresence } from 'framer-motion';
import type { ModuleData, ModuleNavItem } from './types';

import TopBar from './components/TopBar';
import ExplanationPanel from './components/ExplanationPanel';
import CodeViewer from './components/CodeViewer';
import CompletionPage from './components/CompletionPage';

function getLanguageFromPath(path: string): string {
  const extension = path.split('.').pop()?.toLowerCase();
  const languages: Record<string, string> = {
    py: 'python',
    js: 'javascript',
    jsx: 'jsx',
    ts: 'typescript',
    tsx: 'tsx',
    json: 'json',
    css: 'css',
    html: 'markup',
    md: 'markdown',
    rs: 'rust',
    sh: 'bash',
    yml: 'yaml',
    yaml: 'yaml',
    sql: 'sql'
  };
  return languages[extension || ''] || 'text';
}

function getExampleNotes(code: string, notes?: Record<number, string>): Record<number, string> {
  if (notes && Object.keys(notes).length > 0) {
    return notes;
  }

  const examples: Record<number, string> = {};
  const lines = code.split('\n');
  const candidates = lines
    .map((line, index) => ({ line: line.trim(), index }))
    .filter(({ line }) => /^(from |import |class |def |function |const |export |async |fn |struct )/.test(line))
    .slice(0, 3);

  candidates.forEach(({ index, line }) => {
    examples[index] = `Nota di esempio: questa riga introduce un elemento importante del modulo (${line.slice(0, 42)}${line.length > 42 ? '…' : ''}).`;
  });

  return examples;
}

export default function App() {
  const { data, loading, error } = useRepoData();

  const [currentIndex, setCurrentIndex] = useState(0);
  const [direction, setDirection] = useState(1);
  const [studiedFiles, setStudiedFiles] = useState<Set<string>>(new Set());

  const rawModules = data?.raw_modules || [];
  const totalFiles = rawModules.length;
  const studiedCount = rawModules.filter((_, index) => studiedFiles.has(String(index))).length;
  const firstUnstudiedIndex = rawModules.findIndex((_, index) => !studiedFiles.has(String(index)));
  const modules: ModuleNavItem[] = [
    {
      index: 0,
      title: 'Panoramica progetto',
      path: 'Introduzione al repository',
      studied: studiedFiles.has('root')
    },
    ...rawModules.map((module, index) => ({
      index: index + 1,
      title: module.file.split('/').pop() || module.file,
      path: module.file,
      studied: studiedFiles.has(String(index))
    }))
  ];

  const canGoPrev = currentIndex > 0;
  const canGoNext = Boolean(data && currentIndex <= totalFiles);
  const isCompletionPage = currentIndex > totalFiles;

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target;
      if (
        target instanceof HTMLElement &&
        (target.isContentEditable || target.closest('input, textarea, select, [contenteditable="true"]'))
      ) {
        return;
      }

      if (e.key === 'ArrowRight' && canGoNext) {
        setDirection(1);
        setCurrentIndex((prev) => prev + 1);
      } else if (e.key === 'ArrowLeft' && canGoPrev) {
        setDirection(-1);
        setCurrentIndex((prev) => prev - 1);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [canGoNext, canGoPrev]);

  const handleToggleStudy = (pathOrId: string) => {
    const updated = new Set(studiedFiles);

    if (updated.has(pathOrId)) {
      updated.delete(pathOrId);
    } else {
      updated.add(pathOrId);
    }

    setStudiedFiles(updated);
  };

  const goNext = () => {
    if (canGoNext) {
      setDirection(1);
      setCurrentIndex((prev) => prev + 1);
    }
  };

  const goPrev = () => {
    if (canGoPrev) {
      setDirection(-1);
      setCurrentIndex((prev) => prev - 1);
    }
  };

  const goToModule = (index: number) => {
    if (index !== currentIndex) {
      setDirection(index > currentIndex ? 1 : -1);
      setCurrentIndex(index);
    }
  };

  const resumeUnstudied = () => {
    goToModule(firstUnstudiedIndex === -1 ? 0 : firstUnstudiedIndex + 1);
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#F7F7F7] text-[#11151C]">
        <div className="text-2xl font-bold animate-pulse">
          Loading...
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#F7F7F7] text-red-500">
        <div className="max-w-md p-6 border border-red-500 rounded-lg bg-red-50">
          <h2 className="text-xl font-bold mb-2">Errore di Connessione</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  let currentModule: ModuleData;
  let isCurrentStudied: boolean;
  let lines: string[];

  if (currentIndex === 0) {
    currentModule = {
      path: "project/overview",
      title: "EXECUTIVE SUMMARY",
      explanation: data.narrative || "Resume not available",
      code_snippet: data.tree_structure || "Tree not available",
      notes: {}
    };
    isCurrentStudied = studiedFiles.has("root");
    lines = (data.tree_structure || "").split('\n');
  } else {
    const moduleIndex = currentIndex - 1;
    const fileData = rawModules[moduleIndex];
    const filePath = fileData?.file || "Path Sconosciuto";

    currentModule = {
      path: filePath,
      title: filePath.split('/').pop()?.toUpperCase() || "FILE DETAILS",
      explanation: fileData?.explanation || "Spiegazione non trovata nel JSON per questo file.",
      code_snippet: fileData?.code_snippet || "Codice non trovato.",
      notes: getExampleNotes(fileData?.code_snippet || "", fileData?.notes)
    };

    isCurrentStudied = studiedFiles.has(String(moduleIndex));
    lines = (fileData?.code_snippet || "").split('\n');
  }

  const slideVariants = {
    enter: (dir: number) => ({ x: dir > 0 ? 80 : -80, opacity: 0 }),
    center: { x: 0, opacity: 1 },
    exit: (dir: number) => ({ x: dir > 0 ? -80 : 80, opacity: 0 })
  };

  return (
    <div className="min-h-screen w-full overflow-x-hidden bg-slate-50 flex flex-col relative select-none xl:h-screen xl:overflow-y-hidden">
      <TopBar
        repositoryTitle={data.title}
        currentIndex={currentIndex}
        totalFiles={totalFiles}
        studiedCount={studiedCount}
        modules={modules}
        canGoPrev={canGoPrev}
        canGoNext={canGoNext}
        onPrev={goPrev}
        onNext={goNext}
        onSelectModule={goToModule}
        isStudied={isCurrentStudied}
        isFirstSlide={currentIndex === 0}
        showStudyButton={!isCompletionPage}
        onToggleStudy={() => handleToggleStudy(currentIndex === 0 ? "root" : String(currentIndex - 1))}
      />

      <main className="flex-1 flex items-center justify-center relative w-full overflow-x-hidden z-10 px-2 py-4 sm:px-4 xl:min-h-0">
        <div className="w-full max-w-[1700px] mx-auto px-2 sm:px-3 xl:px-10 py-2 xl:h-full xl:min-h-0 flex flex-col justify-center">
          <AnimatePresence mode="wait" custom={direction}>
            {isCompletionPage ? (
              <motion.div
                key="completion"
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.35, ease: "easeOut" }}
              >
                <CompletionPage
                  repositoryTitle={data.title}
                  studiedFiles={studiedCount}
                  totalFiles={totalFiles}
                  onResumeIncomplete={resumeUnstudied}
                />
              </motion.div>
            ) : (
              <motion.div
                key={currentIndex === 0 ? "root" : String(currentIndex - 1)}
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.35, ease: "easeOut" }}
                className="grid grid-cols-1 xl:grid-cols-12 gap-4 xl:gap-6 xl:h-full xl:min-h-0"
              >
                <div className="xl:col-span-5 flex flex-col xl:h-full xl:min-h-0 justify-between">
                  <ExplanationPanel module={currentModule} isOverview={currentIndex === 0} />
                </div>

                <div className="xl:col-span-7 xl:h-full xl:min-h-0 flex flex-col">
                  <CodeViewer
                    lines={lines}
                    notes={currentModule.notes}
                    isTreeLine={currentIndex === 0}
                    isCurrentStudied={isCurrentStudied}
                    language={getLanguageFromPath(currentModule.path)}
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      <footer className="w-full px-4 sm:px-6 pb-3 flex justify-center text-center text-xs text-slate-400 z-20 shrink-0">
        <div>Usa le frecce ← → oppure l’indice per esplorare e ritrovare le schede</div>
      </footer>
    </div>
  );
}