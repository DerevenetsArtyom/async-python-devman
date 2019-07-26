# Async Chat Client

This program is a chat client that has graphical user interface based on [Tkinter GUI](https://docs.python.org/3/library/tkinter.html) and uses the [asyncio](https://docs.python.org/3/library/asyncio.html) module.  
It uses especially asyncio [streams](https://docs.python.org/3/library/asyncio-stream.html) and [queues](https://docs.python.org/3/library/asyncio-queue.html).  
Asyncio tasks are managed with [aionursery](https://pypi.org/project/aionursery/). 

Main features:

* new user registration in chat with saving user credentials in a .env file
* existing user authentication in chat
* reading chat messages
* sending chat messages
* automatic reconnection in case of disconnection
* writing chat messages to a text file


## How to install

Python 3.7 and libraries from **requirements.txt** should be installed.  
Use virtual environment tool, for example **virtualenv**

```bash
virtualenv virtualenv_folder_name
source virtualenv_folder_name/bin/activate
pip install -r requirements.txt
```

Put all necessary parameters to **.env** file.  
There is an example **.env.example**.  
This is default parameters and you can change them by CLI arguments.

```
MINECHAT_SERVER_HOST = 'minechat.dvmn.org'
MINECHAT_SERVER_READ_PORT = 5000
MINECHAT_SERVER_WRITE_PORT = 5050
MINECHAT_HISTORY = 'history.txt'
```

If you are registered user, add your token to **.env** file:
```
MINECHAT_TOKEN = 'your token'
```


## Chat Client Module

If you a new user, this module allows you to register in the chat and save the received user credentials in a .env file.  
In the window, you should enter your preferred nickname and click on the "OK" button. 

![Chat Client](screenshots/register.jpg?raw=true "Chat Client")

This module allows you to read and write messages in the chat with the pre-authorization of the user using the authorization token.

![Chat Client](screenshots/chat.jpg?raw=true "Chat Client")

### How to set up

```bash

$ python main.py -h
usage: main.py [-h] [--host HOST] [--read-port READ_PORT]
               [--write-port WRITE_PORT] [--token TOKEN] [--history HISTORY]

If an arg is specified in more than one place, then commandline values
override environment variables which override defaults.

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           Host for connecting to chat [env var: MINECHAT_SERVER_HOST]
  --read-port READ_PORT  
                        Port for connecting to chat for reading messages. 
                        Default: 5000 
                        [env var: MINECHAT_SERVER_READ_PORT]
  --write-port WRITE_PORT
                        Port for connecting to chat for writing messages.
                        Default: 5050 
                        [env var: MINECHAT_SERVER_WRITE_PORT]
  --token TOKEN         User token for authorisation in chat [env var: MINECHAT_TOKEN]
  --history HISTORY     Filepath for save chat messages. Default: history.log [env var: MINECHAT_HISTORY]

```

### How to launch

Run **main.py** with arguments. Also you can use environment variables as parameters by default.

```bash

export CHAT_HOST='your.chat.host'
python main.py

```
