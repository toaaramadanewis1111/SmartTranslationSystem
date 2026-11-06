
/* LangoLink – responsive web app
   FastAPI handles translation, vocabulary recommendations and PaddleOCR.
*/

const CONFIG = {
  API_BASE: window.LANGOLINK_API_BASE ||
    `${window.location.protocol}//${window.location.hostname}:8000`
};

const LANGS = [
  { c:'en', n:'English',  ocr:'eng',     tts:'en-US' },
  { c:'ar', n:'Arabic',   ocr:'ara',     tts:'ar-SA', rtl:1 },
  { c:'de', n:'German',   ocr:'deu',     tts:'de-DE' },
  { c:'fr', n:'French',   ocr:'fra',     tts:'fr-FR' },
  { c:'es', n:'Spanish',  ocr:'spa',     tts:'es-ES' },
  { c:'ja', n:'Japanese', ocr:'jpn',     tts:'ja-JP' },
  { c:'zh', n:'Chinese',  ocr:'chi_sim', tts:'zh-CN' },
];

const L = c => LANGS.find(l => l.c === c) || LANGS[0];
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

const esc = s => String(s ?? '').replace(/[&<>"]/g, m => ({
  '&':'&amp;',
  '<':'&lt;',
  '>':'&gt;',
  '"':'&quot;'
}[m]));

let S = {
  native:'en',
  learn:'es',
  age:17,
  gender:'Woman',
  goal:'Travel',
  mins:10,
  text:'Where is the train station?',
  context:'',
  res:null,
  speed:1,
  live:false,
  personal:true
};

try {
  Object.assign(S, JSON.parse(localStorage.lango || '{}'));
} catch (e) {}

const save = () => {
  try {
    localStorage.lango = JSON.stringify(S);
  } catch (e) {}
};


/* ---------- icons ---------- */

const P = {
  home:'M3 11l9-8 9 8v10h-6v-6H9v6H3z',
  learn:'M4 5a2 2 0 012-2h13v16H6a2 2 0 00-2 2zM4 19a2 2 0 012-2h13',
  words:'M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01',
  bars:'M5 20V10M12 20V4M19 20v-7',
  plus:'M12 5v14M5 12h14',
  settings:'M4 21v-7m0-4V3m8 18v-9m0-4V3m8 18v-5m0-4V3M2 14h4m4-6h4m4 8h4',
  say:'M4 9v6h4l5 4V5L8 9zM16 9a4 4 0 010 6',
  mic:'M12 3a3 3 0 00-3 3v6a3 3 0 006 0V6a3 3 0 00-3-3zM6 11a6 6 0 0012 0M12 17v4',
  cam:'M4 8h3l2-3h6l2 3h3v11H4zM12 17a3.5 3.5 0 100-7 3.5 3.5 0 000 7',
  back:'M15 5l-7 7 7 7',
  swap:'M7 7h13l-3-3M17 17H4l3 3',
  next:'M9 5l7 7-7 7',
  check:'M5 12l5 5 9-10'
};

const ic = (n, s = 20) =>
  `<svg width="${s}" height="${s}" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" stroke-width="2"
    stroke-linecap="round" stroke-linejoin="round"
    aria-hidden="true"><path d="${P[n]}"/></svg>`;


/* ---------- content ---------- */

const WORDS = [
  {
    en:'reservation',
    es:'la reserva',
    pron:'reh SEHR-bah',
    ex:'Tengo una reserva.',
    tr:'I have a reservation.',
    set:'hotel',
    st:'Saved'
  },
  {
    en:'accommodation',
    es:'el alojamiento',
    pron:'ah loh hah MYEHN toh',
    ex:'Busco alojamiento para dos noches.',
    tr:"I'm looking for accommodation for two nights.",
    set:'hotel',
    st:'Learning'
  },
  {
    en:'departure',
    es:'la salida',
    pron:'sah-LEE dah',
    ex:'¿A qué hora es la salida?',
    tr:'What time is the departure?',
    set:'airport',
    st:'Learning'
  },
  {
    en:'luggage',
    es:'el equipaje',
    pron:'eh kee-PAH heh',
    ex:'¿Dónde recojo mi equipaje?',
    tr:'Where do I collect my luggage?',
    set:'airport',
    st:'Saved'
  },
  {
    en:'passport',
    es:'el pasaporte',
    pron:'pah sah-POHR-teh',
    ex:'Aquí tiene mi pasaporte.',
    tr:'Here is my passport.',
    set:'airport',
    st:'Learning'
  },
];

const LESSONS = {
  hotel: {
    title:'Hotel vocabulary',
    sub:'2 focus words · A confident check in',
    based:'reservation and accommodation',
    cls:'red'
  },
  airport: {
    title:'Airport vocabulary',
    sub:'3 focus words · Ready for takeoff',
    based:'departure, luggage and passport',
    cls:'blue'
  },
};


/* ---------- audio / toast ---------- */

function say(text, code, rate = 1) {
  if (!('speechSynthesis' in window)) {
    return toast('Audio is not supported in this browser');
  }

  const u = new SpeechSynthesisUtterance(text);
  u.lang = L(code).tts;
  u.rate = rate;

  speechSynthesis.cancel();
  speechSynthesis.speak(u);
}

let tt;

function toast(m) {
  const t = $('#toast');

  if (!t) {
    console.log(m);
    return;
  }

  t.textContent = m;
  t.classList.add('on');

  clearTimeout(tt);

  tt = setTimeout(() => {
    t.classList.remove('on');
  }, 2600);
}


/* ---------- FastAPI translation ---------- */

// Sends text to FastAPI and receives the structured translation response.

async function translateText(text, from, to, context) {
  const response = await fetch(`${CONFIG.API_BASE}/translate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      text: text,
      source_lang: from,
      target_lang: to,
      style: 'natural',
      context: context || null
    })
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      data.detail || `Translation failed (${response.status}).`
    );
  }

  S.live = true;

  return data;
}


// Handles normal text translation.

async function run(text) {
  text = String(text || '').trim();

  if (!text) {
    return toast('Type or say something first');
  }

  if (text.length > 500) {
    return toast('Please keep your text under 500 characters.');
  }

  S.text = text;
  save();

  const b = $('#goBtn');

  if (b) {
    b.disabled = true;
    b.classList.add('load');
    b.textContent = 'Translating…';
  }

  try {
    const result = await translateText(
      text,
      S.native,
      S.learn,
      S.context.trim()
    );

    S.res = {
      ...result,
      src: text,
      from: S.native,
      to: S.learn,
      context: S.context.trim(),
      input_type: 'text'
    };

    save();
    go('/result');

  } catch (error) {
    console.error('Translation error:', error);

    toast(
      error instanceof TypeError
        ? `Cannot reach the translation API at ${CONFIG.API_BASE}. Start the backend and try again.`
        : error.message ||
      'Could not connect to the translation server.'
    );

  } finally {
    if (b) {
      b.disabled = false;
      b.classList.remove('load');
      b.textContent = 'Translate & view result';
    }
  }
}


/* ---------- PaddleOCR image translation ---------- */

// Sends the selected image to FastAPI.
// PaddleOCR extracts the text on the backend.
// The extracted text is then translated by the LLM.

async function translateImage(file) {
  if (!file) {
    return toast('Please select an image.');
  }

  // The current OCR service supports English and Arabic only.
  if (!['en', 'ar'].includes(S.native)) {
    return toast(
      'Image translation currently supports English and Arabic source text only.'
    );
  }

  const allowedTypes = [
    'image/png',
    'image/jpeg',
    'image/bmp',
    'image/webp'
  ];

  if (!allowedTypes.includes(file.type)) {
    return toast('Unsupported image format. Use PNG, JPG, BMP or WEBP.');
  }

  const formData = new FormData();

  formData.append('file', file);
  formData.append('source_lang', S.native);
  formData.append('target_lang', S.learn);
  formData.append('style', 'natural');
  if (S.context.trim()) {
    formData.append('context', S.context.trim());
  }

  toast('Extracting text and translating…');

  const imageButton = $('#img');

  if (imageButton) {
    imageButton.disabled = true;
  }

  try {
    const response = await fetch(
      `${CONFIG.API_BASE}/translate/image`,
      {
        method: 'POST',
        body: formData
      }
    );

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(
        data.detail || `Image translation failed (${response.status}).`
      );
    }

    S.live = true;

    S.text = data.extracted_text || '';

    S.res = {
      ...data,
      src: data.extracted_text || '',
      from: S.native,
      to: S.learn,
      context: S.context.trim(),
      input_type: 'image'
    };

    save();

    go('/result');

  } catch (error) {
    console.error('Image translation error:', error);

    toast(
      error instanceof TypeError
        ? `Cannot reach the translation API at ${CONFIG.API_BASE}. Start the backend and try again.`
        : error.message ||
      'Could not process the image.'
    );

  } finally {
    if (imageButton) {
      imageButton.disabled = false;
    }
  }
}


/* ---------- layout ---------- */

const NAV = [
  ['home','home','Translate'],
  ['picks','learn','Learn'],
  ['vocab','words','Words'],
  ['settings','settings','Settings']
];

const GROUP = {
  result:'home',
  travel:'picks',
  hotel:'picks',
  airport:'picks'
};

function shell(r, html) {
  const cur = GROUP[r] || r;

  const nv = n =>
    `<a class="nv ${cur === n[0] ? 'on' : ''}"
      href="#/${n[0]}" aria-label="${n[2]}">
      ${ic(n[1], 22)}
      <span>${n[2]}</span>
    </a>`;

  return `
    <div class="shell">
      <aside class="side">
        <div class="brand">
          <span class="lg">文A</span>Lango<b>Link</b>
        </div>
        ${NAV.map(nv).join('')}
        <a class="btn" href="#/home">
          ${ic('plus')} New translation
        </a>
      </aside>

      <main class="main">${html}</main>

      <nav class="tabbar" aria-label="Main">
        ${nv(NAV[0])}
        ${nv(NAV[1])}
        <a class="fab" href="#/home" aria-label="New translation">
          ${ic('plus', 26)}
        </a>
        ${nv(NAV[2])}
        ${nv(NAV[3])}
      </nav>
    </div>
  `;
}

const pageHeader = (crumb, back = '/home') =>
  `<div class="top">
    <a class="bk" href="#${back}" aria-label="Back">
      ${ic('back')}
    </a>
    <span>Langoconnect › ${crumb}</span>
  </div>`;

const langOpts = sel =>
  LANGS.map(l =>
    `<option value="${l.c}" ${l.c === sel ? 'selected' : ''}>
      ${l.n}
    </option>`
  ).join('');


/* ---------- routes ---------- */

const R = {};
let timer;

R.splash = () => ({
  auth:1,
  html:`
    <div class="splash">
      <span class="lg big">文A</span>
      <div class="typed" id="ty" aria-label="LangoLink">L</div>
    </div>
  `,
  after() {
    const w = 'LangoLink';
    let i = 1;

    timer = setInterval(() => {
      $('#ty').textContent = w.slice(0, ++i);

      if (i >= w.length) {
        clearInterval(timer);
        timer = setTimeout(() => go('/welcome'), 700);
      }
    }, 140);
  }
});

R.welcome = () => ({
  auth:1,
  html:`
    <div class="box center welcome-panel">
      <div class="welcome-art-wrap">
        <svg class="art" viewBox="0 0 200 200" aria-hidden="true">
          <circle cx="100" cy="100" r="92" fill="#17171b"
            stroke="rgba(59,44,255,.95)" stroke-width="4"/>
          <path d="M45 120c20-50 50-70 90-45s10 70-30 60"
            fill="none" stroke="#3b2cff" stroke-width="4"
            stroke-linecap="round"/>
          <circle cx="62" cy="140" r="24" fill="none"
            stroke="#e3122c" stroke-width="4"/>
          <circle cx="142" cy="144" r="24" fill="none"
            stroke="#e3122c" stroke-width="4"/>
          <path d="M55 140h14M135 144h14"
            stroke="#e3122c" stroke-width="4"
            stroke-linecap="round"/>
        </svg>
      </div>

      <div class="welcome-copy">
        <span class="welcome-kicker">Language, reimagined</span>
        <h1 class="welcome-title">Langoconnect</h1>
        <p class="welcome-subtitle">Enhance your language skills with native speakers and real-time practice.</p>
      </div>
      <a class="btn" href="#/login">Start Now</a>
    </div>
  `
});

R.login = () => ({
  auth:1,
  html:`
    <form class="box" id="lf">
      <div class="brand login-brand">
        <svg class="brand-mark" viewBox="0 0 200 200" aria-hidden="true">
          <circle cx="100" cy="100" r="92" fill="#15151a"
            stroke="#3b2cff" stroke-width="4"/>
          <path d="M45 120c20-50 50-70 90-45s10 70-30 60"
            fill="none" stroke="#3b2cff" stroke-width="4"
            stroke-linecap="round"/>
          <circle cx="62" cy="140" r="24" fill="none"
            stroke="#e3122c" stroke-width="4"/>
          <circle cx="142" cy="144" r="24" fill="none"
            stroke="#e3122c" stroke-width="4"/>
          <path d="M55 140h14M135 144h14"
            stroke="#e3122c" stroke-width="4"
            stroke-linecap="round"/>
        </svg>
        Lango<b>Link</b>
      </div>

      <h1 style="text-align:center">Welcome!</h1>
      <p class="mute" style="text-align:center">
        Log in to your account or sign up to start chatting.
      </p>

      <label class="field">
        <span class="lbl">Email</span>
        <input class="in" type="email" autocomplete="email"
          placeholder="you@email.com">
      </label>

      <label class="field">
        <span class="lbl">Password</span>
        <input class="in" type="password"
          autocomplete="current-password" placeholder="••••••••">
      </label>

      <a class="sm mute" href="#/login" style="text-align:right">
        Forget password?
      </a>

      <button class="btn blue">Login</button>

      <div class="chips" style="justify-content:center">
        <span class="chip">G</span>
        <span class="chip">f</span>
        <span class="chip">in</span>
      </div>

      <p class="sm mute" style="text-align:center">
        Don't have an account? No Worries.
        <a href="#/setup/1" style="color:var(--red);font-weight:700">
          Sign up Now
        </a>
      </p>
    </form>
  `,
  after() {
    $('#lf').onsubmit = e => {
      e.preventDefault();
      go('/home');
    };
  }
});

const stepHead = n =>
  `<div class="hero-p">
    <a href="#/${n > 1 ? 'setup/' + (n - 1) : 'login'}">‹ Back</a>
    <span>${n}/4 steps</span>
  </div>
  <div class="prog"><i style="width:${n * 25}%"></i></div>`;

R['setup/1'] = () => ({
  auth:1,
  html:`
    <div class="box">
      ${stepHead(1)}
      <h1>Enhance your language skills!</h1>

      <label class="field">
        <span class="lbl">Native language</span>
        <select id="nat">${langOpts(S.native)}</select>
      </label>

      <label class="field">
        <span class="lbl">Desired language</span>
        <select id="lrn">${langOpts(S.learn)}</select>
      </label>

      <label class="field">
        <span class="lbl">Age: <b id="agev">${S.age}</b></span>
        <input id="age" type="range" min="13" max="80" value="${S.age}">
      </label>

      <div class="field">
        <span class="lbl">Gender</span>
        <div class="chips" id="gen">
          ${['Man','Woman'].map(g =>
            `<button class="chip ${S.gender === g ? 'on' : ''}"
              data-g="${g}">${g}</button>`
          ).join('')}
        </div>
      </div>

      <a class="btn" href="#/setup/2">Next</a>
    </div>
  `,
  after() {
    $('#nat').onchange = e => {
      S.native = e.target.value;
      save();
    };

    $('#lrn').onchange = e => {
      S.learn = e.target.value;
      save();
    };

    $('#age').oninput = e => {
      S.age = +e.target.value;
      $('#agev').textContent = S.age;
      save();
    };

    $$('#gen .chip').forEach(b => {
      b.onclick = () => {
        S.gender = b.dataset.g;
        save();

        $$('#gen .chip').forEach(x => {
          x.classList.toggle('on', x === b);
        });
      };
    });
  }
});

const pick = (n, title, key, opts, next) => () => ({
  auth:1,
  html:`
    <div class="box">
      ${stepHead(n)}
      <h1>${title}</h1>

      <div class="chips" id="pk">
        ${opts.map(o =>
          `<button class="chip ${S[key] == o ? 'on' : ''}"
            data-v="${o}">
            ${key === 'mins' ? o + ' minutes' : o}
          </button>`
        ).join('')}
      </div>

      <a class="btn" href="#/${next}">Next</a>
    </div>
  `,
  after() {
    $$('#pk .chip').forEach(b => {
      b.onclick = () => {
        S[key] = key === 'mins' ? +b.dataset.v : b.dataset.v;
        save();

        $$('#pk .chip').forEach(x => {
          x.classList.toggle('on', x === b);
        });
      };
    });
  }
});

R['setup/2'] = pick(
  2,
  "What's your main goal?",
  'goal',
  ['Travel','Work','Study','Friends'],
  'setup/3'
);

R['setup/3'] = pick(
  3,
  'How long each day?',
  'mins',
  [5,10,15,20],
  'setup/4'
);

R['setup/4'] = () => ({
  auth:1,
  html:`
    <div class="box">
      ${stepHead(4)}
      <h1>Make it yours.</h1>

      <p class="mute">
        Your ${L(S.learn).n} ${S.goal.toLowerCase()} plan is ready.
        Personalization is entirely optional.
      </p>

      <div class="card blue">
        <b>Ready for your next adventure</b>
        <p class="sm">${L(S.native).n} native · ${L(S.learn).n} beginner</p>
        <p class="sm">${S.goal} goal · ${S.mins} minutes a day</p>
      </div>

      <div class="card">
        <h2>Learn from what you translate</h2>
        <p class="sm mute" style="margin:6px 0">
          If you allow it, we'll use recent translation words to suggest
          relevant vocabulary and lessons. For example: reservation and
          luggage can inspire hotel and airport lessons. Optional.
          Change or turn off in Settings anytime.
        </p>

        <button class="btn ${S.personal ? 'blue' : 'dark'}" id="pz">
          ${S.personal ? ic('check') + ' Use recent translations' : 'Use recent translations'}
        </button>

        <p class="sm mute" style="margin-top:6px">
          Allow personalized recommendations.
        </p>
      </div>

      <a class="btn" href="#/home">Finish setup &amp; go home</a>
      <a class="btn line" href="#/home">Skip &amp; go home</a>

      <p class="sm mute center" style="text-align:center">
        Skipping keeps translation and your Travel plan available.
      </p>
    </div>
  `,
  after() {
    $('#pz').onclick = () => {
      S.personal = !S.personal;
      save();
      render();
    };
  }
});


/* ---------- home page ---------- */

R.home = () => ({
  html:`
    <div class="page">
      <div class="brand">
        <span class="lg">文A</span>Lango<b>Link</b>
      </div>

      <h1>Smart translation</h1>

      <div class="langs">
        <label class="field">
          <span class="lbl">From · Native</span>
          <select id="f">${langOpts(S.native)}</select>
        </label>

        <button class="swap" id="sw" aria-label="Swap languages">
          ${ic('swap')}
        </button>

        <label class="field">
          <span class="lbl">To · Learning</span>
          <select id="t">${langOpts(S.learn)}</select>
        </label>
      </div>

      <div class="card">
        <span class="lbl" id="fl">${L(S.native).n}</span>

        <textarea id="tx" maxlength="500"
          placeholder="Type or paste a phrase"
          ${L(S.native).rtl ? 'dir="rtl"' : ''}>${esc(S.text)}</textarea>

        <div class="cnt">
          <span id="ct">${S.text.length} / 500</span>
          <button class="btn sm dark" id="vc" style="width:auto">
            ${ic('mic', 16)} Voice
          </button>
        </div>
      </div>

      <label class="field card">
        <span class="lbl">Context for translation and word picks (optional)</span>
        <textarea class="context-input" id="ctx" maxlength="500"
          placeholder="For example: asking for directions at a train station">${esc(S.context || '')}</textarea>
        <span class="sm mute">
          The model uses this with your phrase and translation to rank relevant words.
        </span>
      </label>

      <div>
        <span class="lbl">Entry methods</span>

        <div class="grid2" style="margin-top:8px">
          <button class="card entry red" id="stt">
            <span class="ico">${ic('mic')}</span>
            <span>
              <b>Speech to text</b><br>
              <span class="sm mute">Speak and translate</span>
            </span>
          </button>

          <button class="card entry blue" id="img">
            <span class="ico">${ic('cam')}</span>
            <span>
              <b>Image translation</b><br>
              <span class="sm mute">Take a photo or upload</span>
            </span>
          </button>
        </div>
      </div>

      <div class="chips">
        <span class="chip red">${S.goal}</span>
        <span class="chip">Beginner ${L(S.learn).n}</span>
      </div>

      <button class="btn" id="goBtn">
        Translate &amp; view result
      </button>
    </div>
  `,
  after() {
    bindEntry();

    $('#f').onchange = e => {
      S.native = e.target.value;
      save();
      render();
    };

    $('#t').onchange = e => {
      S.learn = e.target.value;
      save();
      render();
    };

    $('#sw').onclick = () => {
      [S.native, S.learn] = [S.learn, S.native];
      save();
      render();
    };

    $('#tx').oninput = e => {
      S.text = e.target.value;
      $('#ct').textContent = S.text.length + ' / 500';
    };

    $('#ctx').oninput = e => {
      S.context = e.target.value;
      save();
    };

    $('#goBtn').onclick = () => run($('#tx').value);
  }
});


/* ---------- result page ---------- */

R.result = () => {
  const r = S.res || {
    translation:'',
    src:S.text,
    from:S.native,
    to:S.learn,
    alternatives:[],
    recommended_vocabulary:[]
  };

  // These names match the FastAPI response.
  const v = r.recommended_vocabulary || [];

  const sourceText = r.extracted_text || r.src || S.text;

  const alternatives = r.alternatives || [];

  return {
    html:`
      <div class="page">
        ${pageHeader('Smart translation')}

        <h1>Translate. Then connect.</h1>

        <p class="mute">
          A little ${L(r.to).n} for your next adventure.
          <span class="badge ${S.live ? '' : 's'}">
            ${S.live ? 'LLM connected' : 'Not connected'}
          </span>
        </p>

        <div class="chips">
          <span class="chip">${L(r.from).n}</span>
          <span class="chip on">${L(r.to).n}</span>
        </div>

        <div class="card">
          <span class="lbl">
            ${r.input_type === 'image'
              ? 'Text extracted from image'
              : L(r.from).n}
          </span>

          <p class="big" style="margin-top:6px">
            ${esc(sourceText)}
          </p>
        </div>

        <div class="card blue">
          <span class="lbl" style="color:#cfcbff">
            ${L(r.to).n}
          </span>

          <p class="big" style="margin:6px 0 12px"
            ${L(r.to).rtl ? 'dir="rtl"' : ''}>
            ${esc(r.translation)}
          </p>

          <button class="btn sm dark" id="ls">
            ${ic('say', 16)} Listen
          </button>
        </div>

        ${alternatives.length ? `
          <div class="card">
            <h2>Alternative translations</h2>

            ${alternatives.map(a => `
              <div class="row">
                <span>${esc(a)}</span>
              </div>
            `).join('')}
          </div>
        ` : ''}

        ${v.length ? `
          <div class="card">
            <h2>
              Recommended vocabulary
              <span class="badge s">${esc(r.topic || '')}</span>
            </h2>

            <p class="sm mute">
              Additional words related to this sentence and its topic.
            </p>

            ${v.map(w => `
              <div class="row">
                <div>
                  <b>${esc(w.word)}</b><br>
                  <span class="sm mute">
                    Ranking score:
                    ${Number(w.score).toFixed(3)}
                  </span>
                </div>
              </div>
            `).join('')}
          </div>
        ` : ''}

        <div class="card">
          <h2>Listen in ${L(r.to).n}</h2>

          <p class="sm mute" style="margin:4px 0 10px">
            Speech speed — choose how fast the audio plays.
          </p>

          <div style="display:flex;gap:12px;align-items:center;justify-content:space-between">
            <div class="seg" id="sp">
              ${[0.75,1].map(x => `
                <button class="${S.speed === x ? 'on' : ''}"
                  data-s="${x}">
                  ${x}×
                </button>
              `).join('')}
            </div>

            <button class="btn sm blue" id="rp">Replay</button>
          </div>
        </div>

        <a class="card blue entry" href="#/travel">
          <span>
            <span class="lbl" style="color:#cfcbff">
              Context-aware vocabulary
            </span><br>
            <b>Explore your word picks</b><br>
            <span class="sm">
              Ranked for your phrase${r.context ? ' and context' : ''}.
            </span>
          </span>
          ${ic('next')}
        </a>

        <div>
          <h2 style="margin-bottom:8px">Another translation</h2>

          <div class="grid2">
            <button class="card entry red" id="stt">
              <span class="ico">${ic('mic')}</span>
              <span>
                <b>Speak a phrase</b><br>
                <span class="sm mute">Tap to translate what you say.</span>
              </span>
            </button>

            <button class="card entry blue" id="img">
              <span class="ico">${ic('cam')}</span>
              <span>
                <b>Translate a photo</b><br>
                <span class="sm mute">Take a photo or upload one.</span>
              </span>
            </button>
          </div>
        </div>

        <a class="btn dark" href="#/home">
          Translate another phrase
        </a>
      </div>
    `,

    after() {
      bindEntry();

      const p = () => say(r.translation, r.to, S.speed);

      $('#ls').onclick = p;
      $('#rp').onclick = p;

      $$('#sp button').forEach(b => {
        b.onclick = () => {
          S.speed = +b.dataset.s;
          save();

          $$('#sp button').forEach(x => {
            x.classList.toggle('on', x === b);
          });
        };
      });
    }
  };
};


/* ---------- learning picks ---------- */

R.picks = () => ({
  html:`
    <div class="page">
      ${pageHeader('Your learning picks')}

      <h1>Recommended for you</h1>
      <p class="mute">Turn recent translations into useful words.</p>

      <a class="card blue" href="#/travel">
        <span class="lbl" style="color:#cfcbff">
          ${L(S.native).n} → ${L(S.learn).n}
        </span>

        <h2 style="font-size:1.6rem;margin:4px 0">
          Travel Vocabulary
        </h2>

        <p>Small lessons. A smoother trip.</p>
        <p class="sm" style="margin:8px 0 6px">
          Based on recent translations
        </p>

        <div class="chips">
          ${WORDS.map(w => `
            <span class="chip" style="background:rgba(255,255,255,.2)">
              ${w.en}
            </span>
          `).join('')}
        </div>
      </a>

      <div class="card">
        <a class="row" href="#/hotel">
          <span class="ico" style="background:var(--red)">
            ${ic('home')}
          </span>
          <span style="flex:1">
            <b>Hotel vocabulary</b><br>
            <span class="sm mute">
              2 focus words · Reservation &amp; stays
            </span>
          </span>
          ${ic('next')}
        </a>

        <a class="row" href="#/airport">
          <span class="ico" style="background:var(--blue)">
            ${ic('plus')}
          </span>
          <span style="flex:1">
            <b>Airport vocabulary</b><br>
            <span class="sm mute">
              3 focus words · Ready for takeoff
            </span>
          </span>
          ${ic('next')}
        </a>
      </div>

      <a class="btn dark" href="#/vocab">
        Browse saved vocabulary
      </a>
    </div>
  `
});


/* ---------- context-aware vocabulary ---------- */

R.travel = () => {
  const recent = S.res;
  const recommendations = recent?.recommended_vocabulary || [];

  return ({
  html:`
    <div class="page">
      ${pageHeader('Context-aware vocabulary', '/picks')}

      <h1>Words for your context.</h1>
      <p class="mute">
        Vocabulary recommendations based on your latest translation.
      </p>

      ${recommendations.length ? `
        <div class="card blue">
          <span class="lbl" style="color:#cfcbff">
            Recommended for ${L(recent.to || S.learn).n}
          </span>
          <h2 style="margin:4px 0">Based on your latest translation</h2>
          <p class="sm" style="margin-bottom:10px">
            ${esc(recent.src || S.text)}
            ${recent.context ? `<br>${esc(recent.context)}` : ''}
          </p>
          ${recommendations.map(item => `
            <div class="row">
              <b>${esc(item.word)}</b>
              <span class="sm">Relevance ${Number(item.score).toFixed(2)}</span>
              <button class="sayb" data-vocab-say="${esc(item.word)}"
                data-vocab-lang="${esc(recent.to || S.learn)}"
                aria-label="Listen to ${esc(item.word)}">
                ${ic('say', 16)}
              </button>
            </div>
          `).join('')}
        </div>
      ` : `
        <div class="card">
          <h2>Get personalized word picks</h2>
          <p class="sm mute" style="margin-top:6px">
            Translate a phrase first. The vocabulary model will rank words
            using its meaning, topic, and any context you provide.
          </p>
          <a class="btn dark" href="#/home" style="margin-top:12px">
            Start a translation
          </a>
        </div>
      `}

    </div>
  `,
  after() {
    $$('[data-vocab-say]').forEach(b => {
      b.onclick = () => say(
        b.dataset.vocabSay,
        b.dataset.vocabLang,
        S.speed
      );
    });
  }
  });
};


/* ---------- vocabulary lessons ---------- */

const lesson = k => () => {
  const l = LESSONS[k];
  const ws = WORDS.filter(w => w.set === k);

  return {
    html:`
      <div class="page">
        ${pageHeader('Travel Vocabulary', '/picks')}

        <div class="card ${l.cls}">
          <h1>${l.title}</h1>
          <p>${l.sub}</p>
          <p class="sm" style="margin-top:6px">
            Based on your recent translations of ${l.based}.
          </p>
        </div>

        <p class="mute sm">
          Spanish pronunciation · stressed syllables in CAPS
        </p>

        <div class="grid2">
          ${ws.map(w => `
            <div class="card">
              <div class="row" style="margin:0;padding:0;border:0">
                <b>${w.en}</b>
                <span class="badge ${w.st === 'Saved' ? 's' : ''}">
                  ${w.st}
                </span>
              </div>

              <div class="big" style="margin-top:6px">
                ${w.es}
                <button class="sayb" data-say="${w.es}"
                  aria-label="Listen"
                  style="display:inline-grid;vertical-align:middle">
                  ${ic('say', 16)}
                </button>
              </div>

              <div class="pron">${w.pron}</div>

              <div class="ex">
                <b>${w.ex}</b><br>
                <span class="mute sm">${w.tr}</span>
              </div>
            </div>
          `).join('')}
        </div>

        <a class="btn dark" href="#/vocab">
          Browse saved vocabulary
        </a>
      </div>
    `,
    after() {
      $$('[data-say]').forEach(b => {
        b.onclick = () => say(b.dataset.say, 'es', S.speed);
      });
    }
  };
};

R.hotel = lesson('hotel');
R.airport = lesson('airport');


/* ---------- saved vocabulary ---------- */

R.vocab = () => ({
  html:`
    <div class="page">
      ${pageHeader('Your vocabulary')}

      <h1>Keep the useful words.</h1>
      <p class="mute">Your travel essentials, ready to review.</p>

      <div class="chips">
        <span class="chip on">Travel · 5 words</span>
        <span class="chip">${L(S.native).n} → ${L(S.learn).n}</span>
      </div>

      <div class="card">
        ${WORDS.map(w => `
          <a class="row" href="#/${w.set}">
            <span>
              <span class="mute sm">${w.en}</span><br>
              <b>${w.es}</b>
            </span>
            <span class="sm mute">
              ${LESSONS[w.set].title} ›
            </span>
          </a>
        `).join('')}
      </div>

      <p class="sm mute">
        Keep the article with each Spanish word.
        Open its hotel or airport lesson for examples.
      </p>

      <a class="btn line" href="#/home">Back to home</a>
    </div>
  `
});


/* ---------- settings ---------- */

R.settings = () => ({
  html:`
    <div class="page">
      ${pageHeader('Settings')}

      <h1>Settings</h1>
      <p class="mute">
        Manage your language and account preferences.
      </p>

      <div class="card">
        <h2 style="margin-bottom:12px">Languages</h2>

        <label class="field">
          <span class="lbl">Native language</span>
          <select id="snat">${langOpts(S.native)}</select>
        </label>

        <label class="field" style="margin-top:12px">
          <span class="lbl">Learning language</span>
          <select id="slearn">${langOpts(S.learn)}</select>
        </label>
      </div>

      <div class="card">
        <h2 style="margin-bottom:12px">Learning goal</h2>

        <label class="field">
          <span class="lbl">Focus</span>
          <select id="sgoal">
            ${['Travel','Work','Study','Friends'].map(g => `
              <option ${S.goal === g ? 'selected' : ''}>${g}</option>
            `).join('')}
          </select>
        </label>

        <label class="field" style="margin-top:12px">
          <span class="lbl">Daily time</span>
          <select id="smins">
            ${[5,10,15,20].map(m => `
              <option value="${m}" ${S.mins === m ? 'selected' : ''}>
                ${m} minutes
              </option>
            `).join('')}
          </select>
        </label>
      </div>

      <div class="card">
        <h2>Account</h2>

        <p class="sm mute" style="margin:6px 0 12px">
          This demo does not use a real account.
          Signing out returns to the login screen and keeps
          your preferences on this device.
        </p>

        <a class="btn line" href="#/login">Open login screen</a>

        <button class="btn dark" id="logout" style="margin-top:8px">
          Log out
        </button>
      </div>

      <a class="btn dark" href="#/progress">
        View learning progress
      </a>
    </div>
  `,
  after() {
    $('#snat').onchange = e => {
      S.native = e.target.value;
      save();
    };

    $('#slearn').onchange = e => {
      S.learn = e.target.value;
      save();
    };

    $('#sgoal').onchange = e => {
      S.goal = e.target.value;
      save();
    };

    $('#smins').onchange = e => {
      S.mins = +e.target.value;
      save();
    };

    $('#logout').onclick = () => {
      S.res = null;
      save();
      go('/login');
    };
  }
});


/* ---------- learning progress ---------- */

R.progress = () => ({
  html:`
    <div class="page">
      ${pageHeader('Learning progress', '/settings')}

      <h1>Every word counts.</h1>
      <p class="mute">
        Your beginner ${L(S.learn).n} travel journey.
      </p>

      <div class="chips">
        <span class="chip on">${S.goal}</span>
        <span class="chip">Illustrative progress</span>
      </div>

      <p class="sm mute">
        Sample data to show your future progress —
        not your actual learning history.
      </p>

      <div class="card blue">
        <h2>6 of ${S.mins} minutes</h2>

        <div class="prog"
          style="margin:10px 0;background:rgba(255,255,255,.25)">
          <i style="width:${Math.min(100, 600 / S.mins)}%;background:#fff"></i>
        </div>

        <p class="sm">
          Just ${Math.max(0, S.mins - 6)} more minutes to your daily goal.
        </p>

        <p class="sm">
          ${L(S.native).n} → ${L(S.learn).n} · Beginner · Sample today
        </p>
      </div>

      <div class="stats">
        <div class="stat">
          <b>5</b>
          <span class="sm mute">saved words</span>
        </div>
        <div class="stat">
          <b>4</b>
          <span class="sm mute">context-aware vocabulary</span>
        </div>
        <div class="stat">
          <b>2</b>
          <span class="sm mute">vocabulary lessons</span>
        </div>
      </div>

      <div class="card">
        <h2 style="margin-bottom:12px">Explore your learning</h2>

        <a class="row" href="#/travel">
          <span>
            <b>Context-aware word picks</b><br>
            <span class="sm mute">
              Explore words ranked for your latest translation
            </span>
          </span>
          ${ic('next')}
        </a>

        <a class="row" href="#/vocab">
          <span>
            <b>Saved vocabulary</b><br>
            <span class="sm mute">Your five travel words</span>
          </span>
          ${ic('next')}
        </a>
      </div>

      <a class="btn line" href="#/settings">Back to settings</a>
    </div>
  `
});


/* ---------- speech + photo entry ---------- */

function bindEntry() {
  const SR = window.SpeechRecognition ||
             window.webkitSpeechRecognition;

  const speak = () => {
    if (!SR) {
      return toast(
        'Speech input is not supported here. Try Chrome or Safari.'
      );
    }

    const rc = new SR();

    rc.lang = L(S.native).tts;

    toast('Listening…');

    rc.onresult = e => {
      const transcript = e.results[0][0].transcript;
      run(transcript);
    };

    rc.onerror = () => {
      toast('Could not hear you. Try again.');
    };

    rc.start();
  };

  ['#stt', '#vc'].forEach(s => {
    const b = $(s);

    if (b) {
      b.onclick = speak;
    }
  });

  const im = $('#img');

  if (im) {
    im.onclick = () => {
      if (!['en', 'ar'].includes(S.native)) {
        return toast(
          'Image translation currently supports English and Arabic only.'
        );
      }

      const fileInput = $('#file');

      if (fileInput) {
        fileInput.click();
      } else {
        toast('Image upload input was not found.');
      }
    };
  }
}


// This listener sends the selected image to the FastAPI PaddleOCR endpoint.
// It does NOT run Tesseract.js in the browser.

const fileInput = $('#file');

if (fileInput) {
  fileInput.addEventListener('change', async e => {
    const file = e.target.files[0];

    if (!file) return;

    // Clear the input so the user can select the same file again.
    e.target.value = '';

    await translateImage(file);
  });
}


/* ---------- router ---------- */

function go(path) {
  location.hash = `#${path}`;
}

function render() {
  clearTimeout(timer);
  clearInterval(timer);

  const key = location.hash.replace(/^#\//, '') || 'splash';

  const v = (R[key] || R.splash)();

  $('#app').innerHTML = v.auth
    ? `<div class="auth">${v.html}</div>`
    : shell(key, v.html);

  if (v.after) {
    v.after();
  }

  window.scrollTo(0, 0);
}

addEventListener('hashchange', render);

render();
