// Biblioteca de movimento do motor próprio (11/10/2026). Tudo é função pura do tempo:
// o quadro 812 sai igual sem simular do 0 ao 811, e o render dá o mesmo resultado toda vez.
// Fonte: "How to build motion design studio with Opus 5.5", @0xMovez (passos 07 e 08).
// Carrega como script comum (<script src="motion.js">) e deixa tudo em window.M.

(function () {
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, p) => a + (b - a) * p;

  // Mola amortecida em forma fechada, de 0 a 1. k = rigidez, d = amortecimento.
  function spring(t, k = 170, d = 26) {
    if (t <= 0) return 0;
    const w0 = Math.sqrt(k), z = d / (2 * w0);
    if (z < 1) {
      const wd = w0 * Math.sqrt(1 - z * z);
      return 1 - Math.exp(-z * w0 * t) * (Math.cos(wd * t) + (z * w0 / wd) * Math.sin(wd * t));
    }
    return 1 - Math.exp(-w0 * t) * (1 + w0 * t);
  }

  // As quatro molas da casa. Interface com um fio de rebote; texto grande sem rebote.
  const MOLA = {
    ui: [320, 30],        // botão, toggle, borda da frente de um indicador
    padrao: [170, 26],    // cartão, contêiner, câmera
    pesada: [120, 24],    // tipografia grande, objeto 3D, logo (sem rebote)
    brinca: [220, 14],    // mascote, adesivo (rebote visível; quase nunca nesta casa)
  };
  const mola = (t, tipo = 'padrao') => spring(t, ...MOLA[tipo]);

  // Valor com vários alvos: soma de uma mola por mudança, cada uma no seu tempo.
  // keys: [[tempo, valor], ...] em ordem. Não reinicia a mola: o movimento segue contínuo.
  function track(t, keys, tipo = 'padrao') {
    const [k, d] = Array.isArray(tipo) ? tipo : MOLA[tipo];
    let v = keys[0][1];
    for (let i = 1; i < keys.length; i++) v += (keys[i][1] - keys[i - 1][1]) * spring(t - keys[i][0], k, d);
    return v;
  }

  // Indicador de aba que estica: a borda da frente é mais rígida que a de trás.
  function indicador(t, paradas, largura = 120) {
    const frente = track(t, paradas, [320, 30]);
    const tras = track(t, paradas, [140, 22]);
    return { esq: Math.min(frente, tras), dir: Math.max(frente, tras) + largura };
  }

  // Texto dentro de um contêiner que se transforma: entra depois que a forma começa a mudar
  // e sai antes da próxima mudança.
  function troca(t, tIn, tOut) {
    return Math.min(clamp((t - tIn - 0.08) / 0.12), clamp((tOut - 0.1 - t) / 0.1));
  }

  // Entrada da casa (regra 4a do /motion): sobe com mola e o desfoque some.
  // Devolve { p, y, blur, alpha } pra aplicar no desenho.
  function entra(t, inicio, { tipo = 'padrao', dist = 40, blur = 12 } = {}) {
    const p = mola(t - inicio, tipo);
    return { p, y: (1 - p) * dist, blur: (1 - clamp(p * 1.4)) * blur, alpha: clamp((t - inicio) * 6) };
  }
  // Saída: mais rápida que a entrada.
  function sai(t, inicio, dur = 0.22) {
    const p = clamp((t - inicio) / dur);
    return { p, alpha: 1 - p * p, y: -p * p * 24 };
  }

  // Ruído com semente (mulberry32). Nunca Math.random: o render tem que sair igual toda vez.
  function rng(seed) {
    return () => {
      seed |= 0; seed = seed + 0x6D2B79F5 | 0;
      let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }

  // Loop sem emenda: o último quadro igual ao primeiro.
  const loopT = (t, dur) => ((t % dur) + dur) % dur;

  // Grade de batidas: tempo da batida n (a partir do beats.json, ou de um BPM fixo).
  function batida(n, grade) {
    if (grade && grade.beats && grade.beats.length) {
      const b = grade.beats;
      if (n < b.length) return b[n];
      const passo = b.length > 1 ? b[b.length - 1] - b[b.length - 2] : 0.5;
      return b[b.length - 1] + (n - b.length + 1) * passo;
    }
    const bpm = (grade && grade.bpm) || 120;
    return n * 60 / bpm;
  }

  window.M = { clamp, lerp, spring, MOLA, mola, track, indicador, troca, entra, sai, rng, loopT, batida };
})();
