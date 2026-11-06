export function validateWords(words, duration) {
  if (!Array.isArray(words) || !words.length || words.length > 3000) throw new Error('Prepará entre 1 y 3000 palabras.');
  let end = 0;
  for (const word of words) {
    if (typeof word.text !== 'string' || !word.text.trim() || word.text.length > 120 || !Number.isInteger(word.line) || word.line < 0 || !Number.isFinite(word.start) || !Number.isFinite(word.end) || word.start < end - 0.00001 || word.end <= word.start || word.end > duration + 0.001) throw new Error('Revisá los tiempos: deben estar ordenados, sin superponerse y dentro de la canción.');
    end = word.end;
  }
  return words;
}

export function parseLyrics(text, duration) {
  if (!Number.isFinite(duration) || duration <= 0) throw new Error('Cargá primero una canción.');
  const lines = [];
  let offset = 0;
  for (const raw of text.split(/\r?\n/)) {
    if (/^\[offset:/.test(raw.trim())) { offset = Number(raw.match(/offset:([+-]?\d+)/)?.[1] || 0) / 1000; continue; }
    if (/^\[(ar|ti|al|by|length|re|ve):/i.test(raw.trim())) continue;
    const stamps = [...raw.matchAll(/\[(\d+):([0-5]?\d(?:\.\d+)?)\]/g)];
    const clean = raw.replace(/\[\d+:[\d.]+\]/g, '').trim();
    if (!clean) continue;
    if (stamps.length) for (const stamp of stamps) lines.push({text:clean, start:Number(stamp[1])*60+Number(stamp[2])});
    else lines.push({text:clean, start:null});
  }
  if (!lines.length) throw new Error('Pegá la letra de la canción.');
  const timed = lines.some(line => line.start !== null);
  if (timed && lines.some(line => line.start === null)) throw new Error('En LRC, cada frase debe tener su tiempo [mm:ss.xx].');
  if (timed) lines.sort((a,b) => a.start-b.start);
  const total = lines.reduce((n,l) => n+l.text.split(/\s+/).length,0);
  let cursor = 0;
  const words = lines.flatMap((line, i) => {
    const tokens = line.text.split(/\s+/);
    const start = timed ? line.start + offset : cursor / total * duration;
    const end = timed ? (lines[i+1] ? lines[i+1].start + offset : duration) : (cursor+tokens.length)/total*duration;
    cursor += tokens.length;
    return tokens.map((text,j) => ({text,line:i,start:start+(end-start)*j/tokens.length,end:start+(end-start)*(j+1)/tokens.length}));
  });
  return validateWords(words, duration);
}

export function wordsFromMarks(words, marks, end, duration) {
  if (marks.length !== words.length) throw new Error('Faltan palabras por marcar.');
  return validateWords(words.map((word,i)=>({...word,start:marks[i],end:marks[i+1] ?? end})), duration);
}

export function activeWord(words, time) { return words.findIndex(word => time >= word.start && time < word.end); }
