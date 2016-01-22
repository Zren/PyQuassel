# PyQuassel

Pure python implementation of QuasselClient. Doesn't depend on any PySide/PyQt libraries.

Based on:
 * https://github.com/magne4000/node-libquassel/
 * https://github.com/sandsmark/QuasselDroid/

## Setup

### Install

```bash
git clone https://github.com/Zren/PyQuassel.git
cd PyQuassel
```

### Create `config.py`

```python
host = 'localhost'
port = 4242
username = 'AdminUser'
password = 'PASSWORD'
```

## Run

```bash
python quasselclient.py
```

## Update

```bash
git pull origin master
```
