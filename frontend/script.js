(() => {
  const sidebar      = document.getElementById('sidebar');
  const navItems     = document.querySelectorAll('.nav-item');
  const panels       = {
    home:    document.getElementById('home'),
    search:  document.getElementById('search'),
    readfile:document.getElementById('readfile'),
    pdf:      document.getElementById('pdf'),
    tutor:   document.getElementById('tutor'),
    quiz:    document.getElementById('quiz'),
    contact: document.getElementById('contact'),
  };
  let currentEngine  = 'duckduckgo';
  
  // Clear old results (but NOT the search input)
  function clearAll() {
    // For each panel key, hide its loader and clear its result/output
    const panelKeys = ['search', 'pdf', 'tutor', 'quiz', 'readfile'];
    panelKeys.forEach(key => {
      // loader ids: searchLoader, pdfLoader, etc.
      const loader = document.getElementById(`${key}Loader`);
      if (loader) loader.classList.add('hidden');
  
      let outputEl = null;
      if (key === 'readfile') {
        outputEl = document.getElementById('fileAnswer');
      } else if (key === 'pdf') {
        outputEl = document.getElementById('pdfOutput');
      } else {
        outputEl = document.getElementById(`${key}Output`);
      }
      if (outputEl) outputEl.textContent = '';
    });
  
    // Clear inputs (only if they exist on the current panel)
    const maybeClear = id => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    };
    maybeClear('searchQuery');
    maybeClear('fileInput');
    maybeClear('fileQuestion');
    maybeClear('pdfInput');
  }
  

  function showPanel(name) {
    Object.values(panels).forEach(p => p.classList.add('hidden'));
    clearAll();
    panels[name].classList.remove('hidden');
  }

  // Sidebar nav
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      navItems.forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      const section = item.dataset.section;
      showPanel(section);
  
      if (section === 'search') {
        currentEngine = item.dataset.engine;
        const labels = {
          duckduckgo: '🌐 DuckDuckGo',
          youtube:    '📹 YouTube',
          wikipedia:  '📚 Wikipedia',
          arxiv:      '📄 ArXiv',
          livelookup: '🔎 Live Lookup',
        };
        const input = document.getElementById('searchQuery');
        document.getElementById('searchTitle').textContent = labels[currentEngine] + (currentEngine==='youtube'?' Summary':' Search');
        input.placeholder = `Enter your ${labels[currentEngine].toLowerCase()} query…`;
        document.getElementById('searchBtn').textContent =
          currentEngine === 'youtube' ? '📝 Summarize' : '🔍 Search';
        input.value = '';            // ◀ clear previous text!
      }
  
      if (window.innerWidth < 768) sidebar.classList.add('collapsed');
    });
  });
  
  showPanel('home');

  // SEARCH
  // script.js
  document.getElementById('searchForm').addEventListener('submit', async e => {
    e.preventDefault();

    const q   = document.getElementById('searchQuery').value.trim();
    const out = document.getElementById('searchOutput');
    if (!q) return out.textContent = '❌ Please enter a query.';

    clearAll(); 
    const btn = document.getElementById('searchBtn');
    const ld  = document.getElementById('searchLoader');
    btn.disabled = true; ld.classList.remove('hidden');

    try {
      const res  = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type':'application/json' },
        body: JSON.stringify({ source: currentEngine, query: q })
      });
      const data = await res.json();
      if (data.html) {
        // render the HTML we got back
        out.innerHTML = data.html;
      } else {
        out.textContent = data.error || '❌ Unexpected response';
      }
    } catch(err) {
      out.textContent = '❌ ' + err.message;
    } finally {
      btn.disabled = false; ld.classList.add('hidden');
    }
  });

  // ─── PDF SUMMARIZER ───────────────────────
  document.getElementById('pdfForm').addEventListener('submit', async e => {
    e.preventDefault(); 
    const fileIn = document.getElementById('pdfInput');
    if (!fileIn.files.length) {
      return document.getElementById('pdfOutput').textContent =
        '❌ Please select a PDF.';
    }
    const form = new FormData();
    form.append('file', fileIn.files[0]);
    clearAll();

    const btn = document.getElementById('pdfBtn');
    const ld  = document.getElementById('pdfLoader');
    btn.disabled = true; ld.classList.remove('hidden');

    try {
      const res  = await fetch('/api/pdf-summarize', {method:'POST',body:form});
      const data = await res.json();
      document.getElementById('pdfOutput').textContent =
        data.summary||data.error;
    } catch(err) {
      document.getElementById('pdfOutput').textContent = '❌ '+err.message;
    } finally {
      btn.disabled = false; ld.classList.add('hidden');
    }
  });


  // TUTOR
  document.getElementById('tutorForm').addEventListener('submit', async e => {
    e.preventDefault(); clearAll();
    const out     = document.getElementById('tutorOutput'),
          btn     = document.getElementById('tutorBtn'),
          ld      = document.getElementById('tutorLoader'),
          payload = {
            subject:        document.getElementById('tutorSubject').value.trim(),
            level:          document.getElementById('tutorLevel').value,
            learning_style: document.getElementById('tutorStyle').value,
            background:     document.getElementById('tutorBackground').value.trim(),
            language:       document.getElementById('tutorLanguage').value.trim(),
            question:       document.getElementById('tutorQuestion').value.trim(),
          };
    if (!payload.subject || !payload.level || !payload.question) {
      return out.textContent = '❌ Fill all fields.';
    }
    btn.disabled = true; ld.classList.remove('hidden');
    try {
      const res  = await fetch('/tutor', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      // <-- use innerHTML here
      out.innerHTML = data.html;
    } catch(err) {
      out.textContent = '❌ ' + err.message;
    } finally {
      btn.disabled = false; ld.classList.add('hidden');
    }
  });


  // QUIZ
  document.getElementById('quizForm').addEventListener('submit', async e => {
    e.preventDefault(); clearAll();
    const out = document.getElementById('quizOutput');
    const btn = document.getElementById('quizBtn');
    const ld  = document.getElementById('quizLoader');
    const payload = {
      subject:       document.getElementById('quizSubject').value.trim(),
      level:         document.getElementById('quizLevel').value,
      num_questions: parseInt(document.getElementById('quizCount').value, 10)
    };
    if (!payload.subject || !payload.level)
      return out.textContent = '❌ Fill all fields.';
    btn.disabled = true; ld.classList.remove('hidden');
    try {
      const res = await fetch('/quiz', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      document.getElementById('quizOutput').innerHTML = data.html;
    } catch(err) {
      out.textContent = '❌ ' + err.message;
    } finally {
      btn.disabled = false; ld.classList.add('hidden');
    }
  });

  document.addEventListener('contextmenu', function (e) {
    e.preventDefault();
  });

  document.addEventListener("keydown", function (e) {
    if (e.keyCode === 123) {
      e.preventDefault();
      return false;
    }
    if (e.ctrlKey && e.shiftKey && e.keyCode === 73) {
      e.preventDefault();
      return false;
    }
    if (e.ctrlKey && e.shiftKey && e.keyCode === 74) {
      e.preventDefault();
      return false;
    }
    if (e.ctrlKey && e.shiftKey && e.keyCode === 67) {
      e.preventDefault();
      return false;
    }
    if (e.ctrlKey && e.keyCode === 85) {
      e.preventDefault();
      return false;
    }
  });
  
  
})();