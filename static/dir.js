/* selection */
window.focused = undefined;
window.onfocus = function () {
  if (!window.focused)
    return;
  var filelink = focused.querySelector('.focusable');
  if (filelink)
    filelink.focus();
};

var entries = document.querySelectorAll('.entry-row');
for (var i = 0; i < entries.length; ++i) {
  var tr = entries[i];
  tr.onclick = function () {
    window.focused = this;
    var filelink = this.querySelector('.focusable');
    if (filelink) filelink.focus();
  };

  var filesel = tr.querySelector('.entry-select');
  filesel.style.display = 'none';

  var filelink = tr.querySelector('.file-link');
  if (filelink) {
    filelink.onfocus = function () {
      focused = this.parentElement.parentElement;
      focused.classList.add('focused');
      focused.querySelector('.file-select').checked = true;
    };
    filelink.onblur = function () {
      var tr = this.parentElement.parentElement;
      tr.classList.remove('focused');
      /* TODO: if in existing selection, keep checked */
      tr.querySelector('.file-select').checked = false;
    }
  }
}
document.querySelector('#deh-select').style.display = 'none';

var renamefile = document.querySelector('#file-rename');
if (renamefile) {
  renamefile.onkeyup = function (e) {
    if (e.key === 'Escape')
      window.location = location.pathname;
  };
}

var nooutline = document.createElement('style');
nooutline.innerText = '.entry-name > a:focus { outline: 0 }';
document.head.appendChild(nooutline);

/* keyboard */
var macKbd = (navigator.userAgent.indexOf('Macintosh') >= 0);

document.body.onkeydown = function (e) {
  //console.log('body.onkeydown: ', e);
  var isEditable = e.target.classList.contains('editable');

  var newFocused;
  if (e.shiftKey || e.ctrlKey || e.altKey || e.metaKey) {
    //console.log((e.shiftKey?"shift+":"") + (e.ctrlKey?"ctrl+":"") + 
    //            (e.altKey?"alt+":"") + (e.metaKey?"meta+":"") + e.key);
    if (!isEditable && (macKbd ? e.metaKey : e.ctrlKey)) {
      switch (e.key) {
        case 'c':
          document.querySelector('#do-copy').click();
          break;
        case 'x':
          document.querySelector('#do-cut').click();
          break;
        case 'v':
          document.querySelector('form#cb-paste-form').submit();
          break;
      }
    }
    if (macKbd ? (e.metaKey && e.key == 'Backspace') 
               : (e.key == 'Delete')) {
      if (!isEditable) 
        document.querySelector('#do-delete').click();
    }

    if (macKbd ? e.metaKey : e.altKey) {
      switch (e.key) {
      case 'ArrowUp':
        var path = location.pathname.split('/');
        if (path.length > 2) {
          path.pop();
          window.location = path.join('/');
        }
        break;
      case 'ArrowDown':
        var path = focused.querySelector('.file-link').href;
        window.location = path;
        break;
      }
    }
  } else {
    switch (e.key) {
    case 'ArrowUp':
      if (focused) {
        newFocused = focused;
        do { /* skip rows without "entry-name" */
            newFocused = newFocused.previousElementSibling;
        } while (newFocused && !(newFocused.querySelector('.focusable')));
      } else
        newFocused = document.querySelectorAll('.entry-row:last-child');
      break;
    case 'ArrowDown':
      if (focused) {
        newFocused = focused;
        do { /* skip rows without "entry-name" */
          newFocused = newFocused.nextElementSibling;
        } while (newFocused && !(newFocused.querySelector('.focusable')));
      } else
        newFocused = document.querySelectorAll('.entry-row')[0];
      break;
    case 'Home':
      if (!isEditable) newFocused = document.querySelector('.entry-row');
      break;
    case 'End':
      if (!isEditable) newFocused = document.querySelector('.entry-row:last-child');
      break;
    case 'F2':
      if (focused) {
        var rename = focused.querySelector('.entry-rename a');
        if (rename) rename.click();
      }
      break;
    default:
      console.log(e.key + ' is down');
    }
  }
  /* focus next */
  if (newFocused) {
    var focusable = newFocused.querySelector('.focusable');
    if (focusable) focusable.focus();
    focused = newFocused;
  }
};
