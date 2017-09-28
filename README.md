# Cops & Robbers Coding Challenge

_Cops & Robbers_ is a competitive coding challenge that tests your knowledge of graph algorithms, data structures, and game theory. The goal of _Cops & Robbers_ is to make coding challenges more directly competitive and intense. Moreover, we want this to be a really enjoyable coding challenge where we know people can walk away feeling accomplished. See the brief below to learn more about the challenge.

This coding challenge was created in 25 days in preparation for Colgate University's Prep for Tech event. The challenge was incredibly well received, with some students excited to continue building out their solution at home. Every student had designed a solution, and everybody had learned something interesting.

To play the game, I have a demo running at [cops-n-robbers.franklinvannes.com](cops-n-robbers.franklinvannes.com). Create a team (or two) and follow the instructions to get started.


## Design
_Cops & Robbers_ is built upon the Django-channels web framework. I used the channels component to set up web socket connections between the server and the browser clients displaying the game. This means that when a game is running, it can be "livestreamed" to any client that choose to watch. The movement information as determined by the participant code is sent via http requests to and from the server and the participant's computer.

Because of this design, participants can run code against each other in real-time, allowing them to debug during a game, should they choose to do so. Also, this design allows us to scale nicely.

_Cops & Robbers_ uses Redis to cache game data, and MySQL/PostgreSQL to store more persistent information about teams and game outcomes. _Cops & Robbers_ is thread safe and easily scaled horizontally, bar the limits of any MVC application with a RDBMS persistence tier.

## Goals
This repository has been made open-source in order to:
1. Make the challenge accessible to everyone use.
2. Make the challenge available for improvement.

Because this challenge was made in such a short time given its complexity and my college schedule, I couldn't give this challenge the proper testing that it requires. In addition to writing a test set, I am also looking to clean up the code and generate methods for easy deployment.
If you wish to use this challenge, please do! Let me know if I (Franklin) can be of any help setting up.


## The Brief
Pitch your code against other competitors in a battle for Gotham City! The Cops & Robbers coding challenge puts your code in charge of Gotham's finest cops or Gotham's smartest criminals. It's up to the cops to protect the city's banks and snatch up the criminals; it's up to the criminals to loot the banks and strike rich without getting caught, and it's up to you and your team to code the behavior behind either one of the Cops or the Robbers. Teach your cops or robbers how to navigate the city, how to set up patrols, how to evade the police, how to strike rich, or how to get locked up. After 2 hours of coding and snacks, test your code in a tournament style competition to see who really is Gotham's Finest.


In Cops & Robbers, participants are presented with a map of Gotham City: a labyrinth of streets with the locations of several banks marked on the map. This map is simply a node graph. The teams have two hours to learn how to navigate the city, react to events, and build strategies - What happens if their robber is seen by a cop? Should the police scramble to a robbery, or keep their limited resources spread across the city? How can the criminals work as a team to strike rich? How can the cops work together to protect the city? This necessity for strategy means that participants need to build functional, clean, and adaptable code. Moreover, the competitive environment and time limit should make for an intense and enjoyable coding challenge.
