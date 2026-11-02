import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { ArrowLeft, ArrowRight, Check, Lock } from 'lucide-react';

export interface RawModule {
  dir: string;
  path: string;
  title: string;
  tag: string;
  explanation: string;
  code_snippet: string;
  notes: Record<number, string>;
}

const FILES: RawModule[] = [
  {
    dir: "src",
    path: "src/index.js",
    title: "ENTRY POINT: SERVER BOOTSTRAP",
    tag: "ENTRY POINT",
    explanation: "**Summary**\n\n1. A custom color scheme is defined, assigning specific colors and styles to the labels *info*, *warning*, *error*, and *success*.  \n2. This scheme is stored in a theme object that the Rich library can understand.  \n3. A console instance is then created, linking it to the custom theme.  \n4. The console will automatically apply the defined colors whenever those label names are used in output.  \n5. This setup allows consistent, visually distinct messages throughout the application.  \n6. For example, an *info* message will appear in cyan, while a *warning* shows in yellow.  \n7. Errors are highlighted with bold red text, making them stand out.  \n8. Success messages are displayed in bold green, signaling positive outcomes.  \n9. By centralizing the theme, any future style changes require only a single edit.  \n10. The resulting console object can be imported elsewhere to produce themed, readable terminal output.",
    code_snippet: `import express from "express";\nimport { auth } from "./middleware/auth.js";\nimport tasks from "./routes/tasks.js";\n\nconst app = express();\napp.use(express.json());\napp.use(auth);\napp.use("/tasks", tasks);\n\napp.listen(process.env.PORT || 3000);`,
    notes: {
      5: "Senza questo middleware, req.body sarebbe undefined.",
      6: "Da qui in giù ogni richiesta richiede un token valido.",
      7: "Tutte le rotte delle task vivono in routes/tasks.js."
    }
  },
  {
    dir: "src",
    path: "src/middleware/auth.js",
    title: "AUTH GUARD MIDDLEWARE",
    tag: "MIDDLEWARE",
    explanation: "Controlla l’header `Authorization` e blocca le richieste senza token valido[cite: 1].\n\n### Cosa succede\n* Estrae il token dal formato `Bearer <token>`[cite: 1]\n* Se manca, interrompe il flusso e risponde **401**[cite: 1]\n* Se valido, salva l’utente in `req.user` e passa oltre[cite: 1]",
    code_snippet: `export function auth(req, res, next) {\n  const h = req.headers.authorization || "";\n  const token = h.replace("Bearer ", "");\n  if (!token) return res.status(401).end();\n  req.user = verify(token);\n  next();\n}`,
    notes: {
      3: "Ritorno anticipato: la richiesta si ferma qui se non autorizzata[cite: 1].",
      4: "Le rotte successive leggeranno comodamente req.user[cite: 1]."
    }
  },
  {
    dir: "src",
    path: "src/db.js",
    title: "DATABASE CONNECTION POOL",
    tag: "DATABASE",
    explanation: "Apre la connessione al database PostgreSQL e la condivide con tutta l’app[cite: 1].\n\n### Cosa succede\n* Crea un **pool** di connessioni riutilizzabili[cite: 1]\n* Espone una sola funzione, `query(sql, params)`[cite: 1]\n\n> **Da ricordare:** Usa sempre i parametri (`$1`, `$2`) e mai la concatenazione: previene la SQL injection[cite: 1].",
    code_snippet: `import pg from "pg";\n\nconst pool = new pg.Pool({\n  connectionString: process.env.DATABASE_URL,\n});\n\nexport const query = (sql, params) =>\n  pool.query(sql, params);`,
    notes: {
      2: "Il pool evita di riaprire una connessione a ogni richiesta[cite: 1].",
      6: "Unico punto di accesso al DB per tutta l’app[cite: 1]."
    }
  }
];

export default function App() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [direction, setDirection] = useState(1);
  const [studiedFiles, setStudiedFiles] = useState<Set<string>>(new Set());
  const [activeLine, setActiveLine] = useState<number | null>(null);

  const currentModule = FILES[currentIndex];
  const isCurrentStudied = studiedFiles.has(currentModule.path);
  const canGoPrev = currentIndex > 0;
  // Puoi avanzare solo se hai studiato la classe corrente e non sei all'ultimo file
  const canGoNext = isCurrentStudied && currentIndex < FILES.length - 1;

  // Resetta la riga selezionata quando si cambia slide
  useEffect(() => {
    setActiveLine(null);
  }, [currentIndex]);

  // Navigazione anche da tastiera (Frecce Sinistra/Destra)
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
  }, [canGoNext, canGoPrev]);

  const handleToggleStudy = () => {
    const updated = new Set(studiedFiles);
    if (updated.has(currentModule.path)) {
      updated.delete(currentModule.path);
    } else {
      updated.add(currentModule.path);
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

  const lines = currentModule.code_snippet.split('\n');

  // Varianti per l'animazione a scorrimento orizzontale
  const slideVariants = {
    enter: (dir: number) => ({
      x: dir > 0 ? 80 : -80,
      opacity: 0
    }),
    center: {
      x: 0,
      opacity: 1
    },
    exit: (dir: number) => ({
      x: dir > 0 ? -80 : 80,
      opacity: 0
    })
  };

  return (
    <div className="h-screen w-screen overflow-hidden bg-[#F7F7F7] text-[#11151C] font-['Roboto',sans-serif] flex flex-col justify-between relative select-none">

      <div className="fixed top-0 left-0 pointer-events-none w-[100px] h-[65px] ml-4 mt-4 z-0 rounded-[20px] select-none overflow-hidden">
        <img src="/logo_sfondo_blu.png" className="w-full" />
      </div>

      {/* TOP BAR */}
      <header className="w-full max-w-[1440px] h-[15vh] mx-auto px-12 flex flex-col items-center justify-end z-20 gap-4">
        <span className="text-[15px] font-mono font-normal  bg-black/5 text-black/60 px-4 py-2 rounded-full">
          {currentIndex + 1} / {FILES.length}
        </span>

        {/* Controlli di Navigazione Orizzontale */}
        <div className="flex items-center gap-4 mb-1">
          <button
            onClick={goPrev}
            disabled={!canGoPrev}
            title="Modulo precedente"
            className={`w-12 h-12 rounded-full border flex items-center justify-center transition-all duration-200 ${canGoPrev
              ? 'border-[#11151C] text-[#11151C] hover:bg-[#11151C] hover:text-white cursor-pointer active:scale-95'
              : 'border-black/20 text-black/20 cursor-not-allowed'
              }`}
          >
            <ArrowLeft className="w-5 h-5" strokeWidth={1.8} />
          </button>

          <button
            onClick={goNext}
            disabled={!canGoNext}
            title={
              !isCurrentStudied
                ? "Segna come 'studiato' per sbloccare il modulo successivo"
                : "Prossimo modulo"
            }
            className={`w-12 h-12 rounded-full border flex items-center justify-center transition-all duration-200 ${canGoNext
              ? 'border-[#11151C] text-[#11151C] hover:bg-[#11151C] hover:text-white cursor-pointer shadow-sm active:scale-95'
              : 'border-black/20 text-black/25 cursor-not-allowed'
              }`}
          >
            <ArrowRight className="w-5 h-5" strokeWidth={1.8} />
          </button>
        </div>
      </header>

      {/* AREA CENTRALE CAROSELLO CON PANNELLI LATERALI "PEEK" */}
      <div className="flex-1 flex items-center justify-center relative w-full overflow-hidden z-10 my-2">

        {/* PEEK SINISTRO (Scorcio scuro del modulo precedente) */}
        <div
          onClick={goPrev}
          className={`fixed left-0 top-1/2 -translate-y-1/2 w-[46px] xl:w-[65px] h-[45vh] bg-[#787C82] rounded-r-[36px] transition-all duration-500 z-20 ${canGoPrev
            ? 'opacity-90 hover:w-[70px] cursor-pointer'
            : 'opacity-0 pointer-events-none -translate-x-full'
            }`}
          title={canGoPrev ? "Torna al modulo precedente" : ""}
        />

        {/* CONTENITORE PRINCIPALE SLIDE */}
        <div className="w-full max-w-[1700px] mx-auto px-16 xl:px-20 h-[50vh] flex flex-col justify-center">
          <AnimatePresence mode="wait" custom={direction}>
            <motion.div
              key={currentModule.path}
              custom={direction}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.35, ease: "easeOut" }}
              className="grid grid-cols-12 gap-8 h-full items-start"
            >

              {/* COLONNA SINISTRA (5/12): Doppia Card Nome Classe + Bottone Studiato sotto */}
              <div className="col-span-5 flex flex-col h-full justify-between">

                {/* Contenitore Esterno Grigio Chiaro */}
                <div className="w-full h-[calc(100%-52px)] bg-[#F4F4F4] rounded-[36px] p-4">
                  {/* Contenitore Interno */}
                  <div className="w-full max-h-[350px] rounded-[26px] p-7 flex flex-col overflow-y-auto select-text bg-[#F4F4F4]">

                    <div className="flex items-center justify-between gap-2 mb-2">
                      <span className="font-mono text-xs text-black/50">
                        {currentModule.path}
                      </span>
                      <span className="text-[10px] font-bold tracking-widest uppercase px-2.5 py-0.5 rounded-full bg-black/5 text-black/70">
                        {currentModule.tag}
                      </span>
                    </div>

                    <h2 className="text-2xl lg:text-[28px] font-bold tracking-tight text-[#11151C] mb-5 uppercase leading-snug">
                      {currentModule.title}
                    </h2>

                    <div className="prose prose-sm lg:prose-base prose-slate max-w-none text-[#222] prose-headings:text-xs prose-headings:uppercase prose-headings:tracking-widest prose-headings:text-black/50 prose-headings:mt-5 prose-headings:mb-2 prose-p:leading-relaxed prose-li:my-0.5">
                      <ReactMarkdown>
                        {currentModule.explanation}
                      </ReactMarkdown>
                    </div>

                  </div>
                </div>

                {/* BOTTONE "studiato" */}
                <div className="flex justify-end items-center pt-3 pr-2">
                  <button
                    onClick={handleToggleStudy}
                    className={`px-8 py-1.5 rounded-full border text-sm font-medium tracking-wide transition-all duration-200 flex items-center gap-2 cursor-pointer ${isCurrentStudied
                      ? 'bg-[#4E7D34] border-[#4E7D34] text-white shadow-sm'
                      : 'bg-transparent border-[#4E7D34] text-[#4E7D34] hover:bg-[#4E7D34]/10'
                      }`}
                  >
                    {isCurrentStudied && <Check className="w-3.5 h-3.5" strokeWidth={3} />}
                    studiato
                  </button>
                </div>

              </div>

              {/* COLONNA DESTRA (7/12): Monolite Nero*/}
              <div className="col-span-7 h-[calc(100%-52px)] bg-[#0B0F17] rounded-[36px] p-7 flex flex-col justify-between shadow-xl overflow-hidden select-text border border-white/5">

                {/* Header Interno del Codice */}
                <div className="flex items-center justify-between pb-4 mb-2 border-b border-white/10 shrink-0">
                  <span className="font-mono text-xs text-slate-400">
                    {currentModule.path}
                  </span>
                  <span className="text-[11px] font-mono text-slate-500">
                    Clicca sulle righe evidenziate per i dettagli
                  </span>
                </div>

                {/* Corpo del Codice */}
                <div className="flex-1 overflow-auto py-2 font-mono text-[14px] leading-[1.85]">
                  {lines.map((line, i) => {
                    const hasNote = Boolean(currentModule.notes[i]);
                    const isSelected = activeLine === i;

                    return (
                      <div
                        key={i}
                        onClick={() => hasNote && setActiveLine(isSelected ? null : i)}
                        className={`flex items-baseline px-4 transition-colors whitespace-pre ${hasNote
                          ? isSelected
                            ? 'bg-blue-500/25 text-white border-l-2 border-blue-400 cursor-pointer'
                            : 'bg-white/[0.04] text-slate-100 hover:bg-white/[0.09] border-l-2 border-blue-400/50 cursor-pointer'
                          : 'text-slate-300 border-l-2 border-transparent'
                          }`}
                      >
                        <span className="w-8 shrink-0 text-slate-600 select-none text-xs text-right pr-4">
                          {i + 1}
                        </span>
                        <span>{line || ' '}</span>
                      </div>
                    );
                  })}
                </div>

                {/* Box "Sussurro" per la riga selezionata */}
                <div className="pt-4 mt-2 border-t border-white/10 min-h-[52px] flex items-center shrink-0">
                  {activeLine !== null && currentModule.notes[activeLine] ? (
                    <div className="text-xs lg:text-sm text-slate-200 flex items-center gap-2">
                      <span className="text-blue-400 font-mono font-bold">
                        Riga {activeLine + 1} →
                      </span>
                      <span>{currentModule.notes[activeLine]}</span>
                    </div>
                  ) : (
                    <div className="text-xs text-slate-500 flex items-center gap-2">
                      {!isCurrentStudied ? (
                        <>
                          <Lock className="w-3.5 h-3.5 text-slate-500" />
                          <span>
                            Esplora il codice e clicca su <b>studiato</b> a sinistra per sbloccare la freccia avanti.
                          </span>
                        </>
                      ) : (
                        <span>
                          Modulo completato! Clicca sulla freccia a destra <b>→</b> per passare al file successivo.
                        </span>
                      )}
                    </div>
                  )}
                </div>

              </div>

            </motion.div>
          </AnimatePresence>
        </div>

        {/* PEEK DESTRO */}
        <div
          onClick={goNext}
          className={`fixed right-0 top-1/2 -translate-y-1/2 w-[46px] xl:w-[65px] h-[45vh] bg-[#EFEFEF] rounded-l-[36px] transition-all duration-500 z-20 flex items-center justify-center ${currentIndex < FILES.length - 1
            ? canGoNext
              ? 'opacity-100 hover:w-[70px] cursor-pointer shadow-md'
              : 'opacity-50 cursor-not-allowed'
            : 'opacity-0 pointer-events-none translate-x-full'
            }`}
          title={
            canGoNext
              ? "Vai al prossimo modulo"
              : "Completa prima questo modulo cliccando su 'studiato'"
          }
        >
          {!canGoNext && currentIndex < FILES.length - 1 && (
            <Lock className="w-4 h-4 text-black/25" />
          )}
        </div>

      </div>

      {/* FOOTER MINIMALE */}
      <footer className="w-full px-12 pb-5 flex justify-end items-center text-xs text-black/40 z-20 shrink-0">
        <div>Usa le frecce in alto a destra o la tastiera (← →) per navigare</div>
      </footer>
    </div>
  );
}