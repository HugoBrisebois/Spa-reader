# Spa-reader

the custom modern ereader note and reading status tracker for kindles and kobos

## why build this

i wanted to build this project so that i could track what i was reading and make the transition from tracking kindle metadata to tracking kobo metadata.

## Current features

- Kindle My Clippings.txt file parsing
- book cover loading and displaying
- database management and logging
- maybe more not sure

## future features

- [ ] auto handle Kindle My Clippings.txt for parsing
- [ ] auto scaling of the app
- [ ] kobo database injestion
- [ ] add fullscreen
- [ ] make it so that it can be hosted in docker or run directly on device
- [ ] make the program make the database file

## how to run

go to https://github.com/HugoBrisebois/Spa-reader/releases/tag/v0.1.0
and download the binary, built on x86_64 most likely built for it too.
after downloading, move the file to the place you want to run it from and then make a `books.db` file in the same directory, this way the program and run properly and can query as well as write to the database, this is not yet done by the program. from there just run it! just make sure you have a My Clippings.txt file, i am not providing one for testing pruposes because they all contain personal information not worth putting out into the world and is unique to every reader.
