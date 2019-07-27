# Asynchronous Python

# Table of contents
* ## [1. Game about space and what is going on there...](01.async_console_game/README.md)
    Simple console game about the spaceship in open space. Based on coroutines with using `curses` module.  
    Points were implemented: 
    * own custom game engine
    * animation of stars and ship
    * user interaction via arrow keys on the keyboard
* ## [2. Through garbage to stars!](02.through_garbage_to_stars/README.md)
    The first part of the game turned out to be relaxing and meditatively utopian, so fans of actions will call it boring.  
    It's time to add a mode with guns: explosions, asteroids, satellites, hot pieces of plating.  

    Transfer the players in 2000 - satellite, garbage and coke bottles.  
    Let them dodge obstacles and think about the behavior of humanity!  
    
    And when it comes to understanding - put everyone in 2020.  
    And give the laser gun on the rocket nose.  
    Let the players together annihilate the rubbish heaps, freeing up space for new great achievements.  
    Points were implemented: 
     * custom garbage generator
     * add ability to explode garbage with embedded gun
     * improved movement mechanics of spaceship
     * calculating collisions of spaceship with obstacles
     * game becomes harder as time goes by
* ## [3. I need your photos](03.photo_sharing/async-download-service/README.md)
    Could you share some photos?
    What happens when you click the Download button in Dropbox? 
    How does he manage in one instant to compress gigabytes into the archive and start downloading to your computer? 
    This task requires to write the code for the “Download” button, and learn everything from your own experience.
    
    Django? Flask? Or maybe aiohttp?
    aiohttp server needs to be started. This is the most popular Python framework with asynchronous code support.
    
    New about old: HTTP
    Did you know that the HTTP response does not have to be prepared entirely? 
    This task requires to archive the files on the fly, in pieces, and immediately give these pieces to the client for download.
    
    Make a script that allows you to download all the photos from a landing page in one click.
    
    * launch the site
    * archive files
    * make the code asynchronous

* ## [4. Connect to the underground chat](04.underground_chat/README.md)
    This is a client for an anonymous chat - the message history is not saved, you can enter and exit at any time.
    Messages should arrive instantly, and if the Internet suddenly turns off, the application should reconnect automatically.
    Program through the command line is able to do:

    * connect to chat
    * read users messages 
    * save chat history to log file
    * authorize existing user by token
    * create new account with provided username
    * join the conversation and write to chat

* ## [5. Enhanced underground chat with GUI](05.underground_chat_client/README.md)
    This program is a chat client that has graphical user interface based on [Tkinter GUI](https://docs.python.org/3/library/tkinter.html) and uses the [asyncio](https://docs.python.org/3/library/asyncio.html) module.  
    It uses asyncio [streams](https://docs.python.org/3/library/asyncio-stream.html) and [queues](https://docs.python.org/3/library/asyncio-queue.html) features in particular.  
    Asyncio tasks are managed with [aionursery](https://pypi.org/project/aionursery/). 
    
    Main features:
    * registration of new user in chat with saving credentials to .env file
    * authentication of existing user in chat by token
    * reading chat messages
    * sending chat messages
    * automatic reconnection in case of disconnection
    * writing chat messages to a text file
