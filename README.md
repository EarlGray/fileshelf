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

Now check [http://localhost:8021](http://localhost:8021)

## Docker

Inside this repository directory (or just use the supplied [docker-compose.yml](docker-compose.yml)):

```sh
$ docker-compose up
```

and check [http://localhost:8021](http://localhost:8021)

## Configuration

FileShelf can take a configuration file as a parameter:

```
$ python index.py conf.json
```

Configuration options are listed here: [fileshelf/app.py#L19](https://github.com/EarlGray/fileshelf/blob/master/fileshelf/app.py#L19)

An example of simple configuration:

```json
{
    "host": "0.0.0.0",
    "port": 8021,
    "debug": true,
    "storage_dir": "~/fileshelf"
}
```
