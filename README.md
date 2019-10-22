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

* ## [6. Filtering the Internet at the speed of light](06.news-filtering/README.md)
    Are you tired of the fake news on the Internet? Now there is a chance to get even with them. 
    There will be a crawler, which will be held on the sites and will make its own rating of jaundice. 
    The more expressive words, brightly negative or enthusiastically positive phrases in the text, 
    the lower the rating of the article and the less desire to read it.
    Thanks to the asynchronous nature of it will gain a huge speed, limited only by the network connection.

    The task of the plugin to the browser is to scan a page of the news site and find all the links to the articles. 
    Next, a web service comes into play: it downloads the text of the article, 
    conducts analysis and makes its own verdict - assigns a rating of jaundice. 
    The information is sent back to the plugin and it displays the rating directly on the page of the news site.

    Algorithms of text evaluation are ready, the plugin is on the way, there is no backend. 

    * Evaluation the objectivity of the articles
    * Acceleration the analysis to the maximum
    * JSON-API for browser plugin

* ## [7. Watching the buses](07.buses-on-the-map/README.md)
    There is a socially and environmentally responsible citizen. He wants to make people use cars less.  
    If we switch to public transport, the traffic jams will be less and the air will be cleaner.  

    That Hero has come up with an application that will make public transport trips more convenient:  
    it will show in real time where this transport is located.   
    Then you can not wait long for the right bus, and come just in time for its arrival.
    
    Hero knows that all buses are equipped with GPS-sensors, which share the location.  
    Their coordinates can be recognized and displayed on the map in the browser.
    There is only one thing left - the server part. Let's help to make the city cleaner!
    
    In order for buses to move around the map, not only do they need coordinates, but they also need to be constantly updated.  
    Moreover, it is necessary to update the position of 20 thousand buses at once.

    * Gather information about the coordinates of buses and other transport
    * Pack it up
    * Send to all browsers connected to the server safely, without lags or hangs
