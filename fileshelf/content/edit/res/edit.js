var editorModes = {
    clike: {
        desc: 'C-like',
        mime: 'text/css',
        fext: 'c,cc,cpp,java,scala'
    },
    css: {
        desc: 'CSS',
        fext: 'css'
    },
    diff: {
        desc: 'Diff',
        fext: 'diff,patch'
    },
    erlang: {
        desc: 'Erlang',
        fext: 'erl'
    },
    forth: {
        desc: 'Forth',
        fext: 'f'
    },
    gas: {
        desc: 'GNU assembly',
        fext: 'S,s,asm'
    },
    go: {
        desc: 'Go',
        fext: 'go'
    },
    groovy: {
        desc: 'Groovy',
        fext: 'groovy'
    },
    haskell: {
        desc: 'Haskell',
        fext: 'hs,lhs'
    },
    javascript: { desc: 'Javascript',
        mime: "application/javascript",
        fext: "js"
    },
    jinja2: {
        desc: 'Jinja2'
    },
    lua: {
        desc: 'Lua',
        fext: 'lua'
    },
    markdown: {
        desc: 'Markdown',
        fext: "md,markdown"
    },
    mbox: {
        desc: 'mbox',
        fext: "mbox"
    },
    mllike: {
        desc: 'Ocaml/SML',
        fext: "ml"
    },
    perl: {
        desc: 'Perl',
        fext: "pl,pm"
    },
    php: {
        desc: 'PHP',
        fext: "php"
    },
    powershell: {
        desc: 'Powershell',
        fext: "ps1"
    },
    python: {
        desc: 'Python',
        mime: "text/x-python",
        fext: 'py',
    },
    r: {
        desc: 'R',
        fext: "r"
    },
    ruby: {
        desc: 'Ruby',
        fext: "rb"
    },
    rust: {
        desc: 'Rust',
        fext: "rs"
    },
    scheme: {
        desc: 'Scheme',
        fext: "scm"
    },
    shell: {
        desc: 'shell',
        mime: "text/x-sh",
        fext: "sh,bash"
    },
    sql: {
        desc: 'SQL',
        fext: "sql"
    },
    swift: {
        desc: 'Swift',
        fext: "swift"
    },
    stex: {
        desc: 'Tex, Latex',
        fext: "tex",
        src:  "https://codemirror.net/mode/stex/stex.js",
    },
    troff: {
        desc: 'Troff',
        fext: "tr"
    },
    verilog: {
        desc: 'Verilog',
        fext: "v"
    },
    vue: {
        desc: 'Vue.js',
        fext: "vue"
    },
    xml: {
        desc: 'XML, HTML',
        mime: "application/xml",
        fext: "xml,htm,html"
    },
    yaml: {
        desc: 'YAML',
        fext: "yaml"
    },
};

(function (modes) {
  var selectMode = document.querySelector('#editor-mode');
  for (var m in modes) {
    var mode = modes[m];
    var opt = document.createElement('option');
    opt.value = m; opt.innerText = mode.desc;
    if ('mime' in mode) { opt.setAttribute('data-mime', mode['mime']); }
    if ('fext' in mode) { opt.setAttribute('data-fext', mode['fext']); }
    if ('src'  in mode) { opt.setAttribute('data-src',  mode['src']); }
    selectMode.appendChild(opt);
  }
})(editorModes);

var editorFonts = [
    "PT Mono",
    "Menlo",
    "Droid Mono",
    "Courier New",
    "Liberation Mono",
];

(function (fonts) {
  var selectFont = document.querySelector('#editor-font');
  for (var i = 0; i < fonts.length; ++i) {
    var opt = document.createElement('option');
    opt.value = opt.innerText = fonts[i];
    selectFont.appendChild(opt);
  }
})(editorFonts);

var the_editor;
var textarea = document.querySelector('#text-editor');

var loadedCache = {};
var loadCodemirror = function (path, loaded, src) {
  if (!src)
    src = data.codemirror_root + "/" + path;

  if (loadedCache[src])
    return loaded();

  var js_el = document.createElement('script');
  js_el.onload = function () {
    loadedCache[src] = true;
    loaded();
  };
  js_el.src = src;
  var page = document.querySelector('#page');
  page.appendChild(js_el);
};

var saveText = function () {
  console.log('saving...');
  var text = the_editor.getValue();
  var url = location.pathname + '?edit=update';

  var saveButton = document.querySelector('#save-btn');
  saveButton.classList.add('save-btn-saving');

  var xhr = new XMLHttpRequest();
  xhr.onreadystatechange = function () {
    if (xhr.readyState !== XMLHttpRequest.DONE)
      return;

    saveButton.classList.remove('save-btn-saving');
    if (xhr.status == 200) {
      the_editor.markClean();
      saveButton.disabled = true;
      console.log('UPDATE: xhr.responseText: ' + xhr.responseText);
    } else {
      saveButton.classList.add('save-btn-failed');
      console.log('UPDATE: xhr.status = ' + xhr.status);
    }
  };
  xhr.onerror = function () {
    console.log('xhr error');
  };
  xhr.open('POST', url);
  xhr.setRequestHeader('Content-Type', 'text/plain');
  xhr.send(text);
};

var quitEditor = function () {
  var path = window.location.pathname.split('/');
  path.pop();
  var url = path.join('/');
  window.location = url;
};

var setupVim = function () {
  /* ex commands */
  CodeMirror.Vim.defineEx('quit', 'q', function (wo, inp) {
    if (the_editor.isClean() || inp.input.endsWith('!')) {
      quitEditor();
    } else {
      var msg = '<span style="color: red">There are unsaved changes</span>';
      the_editor.openNotification(msg, { bottom: true });
    }
  });

  /* key mappings */
  CodeMirror.Vim.map(';', ':', 'normal');

  /* options */
  var checkWrapLines = document.querySelector('input#editor-wrap-lines');
  CodeMirror.Vim.defineOption('wrap', checkWrapLines.checked, 'boolean', [],
    function (val, arg) {
      console.log(arg);
      if (val === undefined)
        return checkWrapLines.checked;

      checkWrapLines.checked = val;
      checkWrapLines.onchange();
    });

  var checkLineNums = document.querySelector('input#editor-line-numbers');
  CodeMirror.Vim.defineOption('number', checkLineNums.checked, 'boolean', [],
    function (val) {
      if (val === undefined)
        return checkLineNums.checked;

      checkLineNums.checked = val;
      checkLineNums.onchange();
    });

  var selectFontFamily = document.querySelector('select#editor-font');
  CodeMirror.Vim.defineOption('font', selectFontFamily.selectedOptions[0],
    'string', [], function (val) {
      if (val === undefined)
        return selectFontFamily.selectedOptions[0].value;
    });
};

window.onload = function () {
  var $ = function () { return document.querySelector(...arguments); }
  var selectMode = $('select#editor-mode');

  var detectMode = function () {
    var the_ext = window.location.pathname.split('.');
    if (the_ext.length < 2)
      return;
    the_ext = (function (a) { return a[a.length-1]; })(the_ext);
    console.log('detecting mode for extension '  + the_ext);

    for (var i = 0; i < selectMode.children.length; ++i) {
      var opt = selectMode.children[i];
      var mime = opt.getAttribute('data-mime');
      if (mime && mime === data.mimetype)
        return i;

      var file_exts = opt.getAttribute('data-fext');
      if (!file_exts) continue;
      file_exts = file_exts.split(',');
      if (file_exts.indexOf(the_ext) >= 0)
        return i;
    }
    return null;
  };

  CodeMirror.commands.save = saveText;

  the_editor = CodeMirror.fromTextArea(textarea, {
      lineNumbers: true
  });
  the_editor.focus();


  /* mode */
  selectMode.onchange = function (event) {
    var mode_changed = function () {
      the_editor.setOption('mode', mode);
      console.log('editor mode changed to ' + (mode ? mode : 'plain'));
    };
    var mode_opt = selectMode.selectedOptions[0];
    var mode = mode_opt.value;
    if (!mode)
      return mode_changed();
    var mode_src = mode_opt.getAttribute('data-src');
    console.log('mode_src = ' + mode_src);

    loadCodemirror('mode/'+mode+'/'+mode+'.min.js', mode_changed, mode_src);
  };
  
  var mode_index = detectMode();
  if (mode_index) {
    var mode_opt = selectMode.options[mode_index];
    console.log('detected mode: '+mode_opt.value+' ('+mode_index+')');
    mode_opt.selected = true;
    selectMode.onchange();
  }

  /* keymap */
  var selectKeymap = $('select#editor-keymap');
  selectKeymap.onchange = function () {
    var keymap_opt = selectKeymap.selectedOptions[0];
    var keymap = keymap_opt.value;

    loadCodemirror('keymap/' + keymap + '.min.js', function () {
      the_editor.setOption('keyMap', keymap);
      if (keymap == 'vim')
        setupVim();
      console.log('editor keymap changed to ' + keymap);
    });

    if (window.localStorage) {
      localStorage.setItem('fileshelf/edit/keymap', keymap);
    }
  };

  var keymap = selectKeymap.selectedOptions[0].value;
  if (window.localStorage) {
    var saved = localStorage.getItem('fileshelf/edit/keymap');
    if (saved) { keymap = saved; }
  }
  console.log('selected keymap: ' + keymap);
  selectKeymap.onchange();

  /* font */
  var selectFontFamily = $('select#editor-font');
  selectFontFamily.onchange = function () {
    var opt = selectFontFamily.selectedOptions[0];
    var val = opt.value;
    if (window.localStorage) { localStorage.setItem('fileshelf/edit/font', val); }

    var cm = $('.CodeMirror');
    cm.style.fontFamily = val;
  };

  if (window.localStorage) {
    var fontFamily = localStorage.getItem('fileshelf/edit/font');
    if (fontFamily) {
      $('option[value="' + fontFamily + '"]').selected = true;
      selectFontFamily.onchange();
    }
  }

  /* font size */
  var selectFontSize = $('input#editor-font-size');
  selectFontSize.onchange = function (event) {
    var fontsize = this.value + 'pt';
    if (window.localStorage) {
      localStorage.setItem('fileshelf/edit/fontsize', this.value);
    }

    var cmdiv = $('.CodeMirror');
    cmdiv.style.fontSize = fontsize;

    console.log('font size changed to ' + fontsize);
  };

  if (window.localStorage) {
    var fontsize = localStorage.getItem('fileshelf/edit/fontsize');
    if (fontsize) { selectFontSize.value = fontsize; }
  }
  selectFontSize.onchange();

  /* show line numbers */
  var checkLineNumbers = $('input#editor-line-numbers');
  var toggleLineNumbers = function () {
    var checked = checkLineNumbers.checked;
    the_editor.setOption('lineNumbers', checked);
    if (window.localStorage) {
      localStorage.setItem('fileshelf/edit/linenum', checked ? 'on' : 'off');
    }
  };
  checkLineNumbers.checked = true;
  if (window.localStorage) {
    if (localStorage.getItem('fileshelf/edit/linenum') === 'off') {
      checkLineNumbers.checked = false;
    }
  }
  checkLineNumbers.onchange = toggleLineNumbers;
  checkLineNumbers.onchange();

  /* line wrap */
  var checkLineWrap = $('input#editor-wrap-lines');
  checkLineWrap.onchange = function () {
    var checked = checkLineWrap.checked;
    the_editor.setOption('lineWrapping', checked);
    if (window.localStorage) {
      localStorage.setItem('fileshelf/edit/linewrap', checked ? 'on':'off');
    }
  };
  checkLineWrap.checked = true;
  if (window.localStorage) {
    if (localStorage.getItem('fileshelf/edit/linewrap') === 'off') {
      checkLineWrap.checked = false;
    }
  }
  checkLineWrap.onchange();

  /* resize */
  var cmdiv = $('.CodeMirror');
  var cmtop = cmdiv.offsetTop;
  cmdiv.style.height = 'calc(100vh - 1em - '+cmtop+'px)';
  the_editor.refresh();

  /* save button */
  var saveButton = $('#save-btn');
  saveButton.onclick = saveText;
  saveButton.disabled = true;
  the_editor.on('change', function () {
    saveButton.disabled = the_editor.isClean();
  });

  /* settings  */
  var settingsButton = $('#settings-btn');
  var settingsTrig = $('#settings-summary');
  settingsButton.onclick = function () { settingsTrig.click(); return false; };
};
