# FileShelf

FileShelf is a simple web-based file manager.


## Features

- fast directory browsing using lightweight pages;
- core functionality works without JavaScript, progressive enhancement; noscript/w3m/elinks compatible;
- file uploading/downloading;
- creating new files/directories, rename/delete, copy/cut/paste files;

File content plugins:
- viewing *pdf* files using your browser;
- playing audio files from a directory;
- editing text files using [CodeMirror](https://codemirror.net/) (with vim mode);
- reading *epub* files using [epub.js](https://github.com/futurepress/epub.js);
- *extensible*: write any file plugin you like!

Optional features:
- offloading large static files to Nginx;
- multiuser setup;
- basic HTTP authentication;


## Install and run

```sh
$ virtualenv -p python3 v3nv
$ . v3nv/bin/activate
(v3nv)$ pip install -r requirements.txt
(v3nv)$ python index.py
```
