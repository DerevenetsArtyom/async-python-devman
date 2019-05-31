# Underground Chat CLI

## Installation
Just `git clone` this repo on your local machine and run it as Python script.  
Python 3.6 and libraries from **requirements.txt** should be installed.

```bash
cd 04.underground_chat/
pip install -r requirements.txt
```
## Quickstart

* Put all necessary parameters to **.env** file.  
There are default parameters for utility and you can override them with explicit CLI arguments.  
You can find template for that in **.env.example** file in that project.
```
SERVER_HOST='minechat.dvmn.org'
SERVER_READ_PORT=5000
SERVER_WRITE_PORT=5050
HISTORY='minechat-history.txt'
TOKEN=''
USERNAME=''
```

* Run **reader.py** or/and **writer.py** with parameters.  
Also you can use environment parameters by default.

```bash
python3.6 reader.py [--host] [--port] [--history]
```

* For **writer.py**, you can use only *token* or *username*, not both.  
If you use *token*, you'll get your *username* after correct authorization.  
If you use *username*, its initialize new user registration and you'll get your *token* interactively.

```bash
python3.6 writer.py [--host] [--port] [--token] [--username] [--message]
```
