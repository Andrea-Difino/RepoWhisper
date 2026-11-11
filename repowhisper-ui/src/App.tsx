import React, { useState, useEffect } from 'react';
import { useRepoData } from './hooks/useRepoData';
import { motion, AnimatePresence } from 'framer-motion';

// Importiamo tutti i componenti puliti
import TopBar from './components/TopBar';
import NavigationPeeks from './components/NavigationPeeks';
import ExplanationPanel from './components/ExplanationPanel';
import CodeViewer from './components/CodeViewer';
import StudyButton from './components/StudyButton';

export default function App() {
  const { data, loading, error } = useRepoData();

  // 1. STATO GLOBALE (Il "Cervello" dell'app)
  const [currentIndex, setCurrentIndex] = useState(0);
  const [direction, setDirection] = useState(1);
  const [studiedFiles, setStudiedFiles] = useState<Set<string>>(new Set());
  const [showGraph, setShowGraph] = useState(false);

  // 2. VARIABILI DERIVATE E LOGICA DI NAVIGAZIONE
  // Ora la chiave reale che usiamo è "raw_modules", e all'interno non è un dizionario
  // con chiave il percorso, ma è un semplice Array di oggetti. 
  // Per mantenere la logica funzionante, usiamo l'indice dell'array come identificatore.
  const rawModules = data?.raw_modules || [];
  const totalFiles = rawModules.length;

  const canGoPrev = currentIndex > 0;
  const canGoNext = Boolean(
    data &&
    studiedFiles.has(currentIndex === 0 ? "root" : String(currentIndex - 1)) &&
    currentIndex <= totalFiles
  );

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
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
  }, [canGoNext, canGoPrev, showGraph]);

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

  // 3. SCHERMATE DI SICUREZZA (Caricamento e Rete)
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#F7F7F7] text-[#11151C]">
        <div className="text-2xl font-bold animate-pulse">
          Sincronizzazione neurale in corso...
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

  // 4. COSTRUZIONE DEL MODULO CORRENTE (Unisce JSON e Interfaccia)
  let currentModule;
  let isCurrentStudied = false;
  let lines: string[] = [];

  if (currentIndex === 0) {
    currentModule = {
      // Per la view, root_id non esiste, diamo semplicemente la path logica
      path: "project/overview",
      title: "EXECUTIVE SUMMARY",
      explanation: data.narrative || data.architecture_summary || "Riassunto non disponibile.",
      code_snippet: data.tree_structure || "Albero non disponibile.",
      notes: {} as Record<number, string>
    };
    isCurrentStudied = studiedFiles.has("root");
    lines = (data.tree_structure || "").split('\n');
  } else {
    // Navighiamo nell'array `raw_modules`. currentIndex 1 corrisponde a rawModules[0]
    const moduleIndex = currentIndex - 1;
    const fileData = rawModules[moduleIndex];
    const filePath = fileData?.file || "Path Sconosciuto";

    currentModule = {
      path: filePath,
      title: filePath.split('/').pop()?.toUpperCase() || "FILE DETAILS",
      explanation: fileData?.explanation || "Spiegazione non trovata nel JSON per questo file.",
      code_snippet: fileData?.code_snippet || "Codice non trovato.",
      notes: {} as Record<number, string> // Mantenuto se un domani il backend inizierà a generarle
    };
    
    // Lo stato dello studio si basa sull'indice numerico (trasformato in stringa)
    isCurrentStudied = studiedFiles.has(String(moduleIndex));
    lines = (fileData?.code_snippet || "").split('\n');
  }

  // 5. ANIMAZIONI FRAMER MOTION
  const slideVariants = {
    enter: (dir: number) => ({ x: dir > 0 ? 80 : -80, opacity: 0 }),
    center: { x: 0, opacity: 1 },
    exit: (dir: number) => ({ x: dir > 0 ? -80 : 80, opacity: 0 })
  };

  // 6. RENDER DEI COMPONENTI
  return (
    <div className="h-screen w-screen overflow-x-hidden bg-[#F7F7F7] flex flex-col relative select-none ">
      <div className="fixed top-0 left-0  overflow-hidden pointer-events-none w-[100px] h-[65px] ml-4 mt-4 z-10 rounded-[20px]">
        <img src="/logo_sfondo_blu.png" className="w-full" alt="Logo" />
      </div>

      <TopBar 
        currentIndex={currentIndex} 
        totalFiles={totalFiles}
        canGoPrev={canGoPrev}
        canGoNext={canGoNext}
        onPrev={goPrev}
        onNext={goNext}
        onToggleGraph={() => setShowGraph(true)}
      />

      <div className="flex-1 flex items-center justify-center relative w-full overflow-x-hidden z-10 my-2">
        <NavigationPeeks 
           canGoPrev={canGoPrev} 
           canGoNext={canGoNext} 
           onPrev={goPrev} 
           onNext={goNext}
           isLastSlide={currentIndex >= totalFiles}
        />

        <div className="w-full max-w-[1700px] mx-auto px-16 xl:px-20 h-[50vh] overflow-hidden flex flex-col justify-center">
          <AnimatePresence mode="wait" custom={direction}>
            <motion.div
              key={currentIndex === 0 ? "root" : String(currentIndex - 1)}
              custom={direction}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.35, ease: "easeOut" }}
              className="grid grid-cols-12 gap-8 h-full"
            >

              <div className="col-span-5 flex flex-col h-full min-h-0 justify-between">
                <ExplanationPanel module={currentModule} />
                <div className="flex justify-end pt-3 pr-2 shrink-0">
                  <StudyButton 
                      isStudied={isCurrentStudied} 
                      onClick={() => handleToggleStudy(currentIndex === 0 ? "root" : String(currentIndex - 1))} 
                      isFirstSlide={currentIndex === 0}
                  />
                </div>
              </div>

              <div className="col-span-7 h-full min-h-0 flex flex-col">
                <CodeViewer 
                  lines={lines} 
                  notes={currentModule.notes} 
                  isTreeLine={currentIndex === 0}
                  isCurrentStudied={isCurrentStudied}
                />
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      <footer className="w-full px-12 pb-5 flex justify-end text-xs text-black/40 z-20 shrink-0">
        <div>Usa le frecce in alto a destra o la tastiera (← →) per navigare</div>
      </footer>
    </div>
  );
}