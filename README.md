# Interactive Fiction CIS-700: Improved Action Castle
Interactive Fiction and Text Generation

## Improved Parser Support 

* support for the Action Castle parser is improved using WordNet for the following commands
```
commands = [
	'wear crown',
	'smell rose',
	'eat fish',
	'light lamp',
	'give fish to troll',
	'propose to the princess',
	'go north',
]
```
* annotations of word senses for these commands results in expanded support for 12524 commands instead of the 7 in the above list
* the improved parser is built on top of the simple string-matching parser; a command is first passed through the simple parser, and if no match is found, it is then passed through the WordNet enhanced list of alternative commands; if no match is found yet again, then a semantically closest alternative command is searched for using Word2Vec embeddings of the user's command and the known set of 12524 commands (similarity between commands must exceed 0.5 for the alternative to be accepted)

### Example 1

Whereas previously 'sniff rose' would have been an unacceptable command, due the parser's improved functionality, the game is now able to map 'sniff rose' to the pre-defined command 'smell rose'. Not also that 'smell flower' relies on the hyponym-hypernym relationship between 'rose' and 'flower' to correctly parse the commmand as being equal to 'smell rose'. Additionally, adding an adjective such as 'fragrant' to the command does not cause the parser to break, since the Word2Vec embedding similarity between 'smell the fragrant flower' and 'smell rose' exceeds 0.5. This makes the parser robust to noisy input.

```
You are standing in a small cottage.
Exits: Out
You see: 
a fishing pole
> go out
You are standing on a lush garden path. There is a cottage here.
Exits: In, North, South
You see: 
a rosebush
	 pick rose
> pick rose
You pick the lone rose from the rosebush.
> sniff rose
It smells sweet.
> smell flower
It smells sweet.
> smell the fragrant flower
It smells sweet.
> exit
I'm not sure what you want to do.
THE GAME HAS ENDED.
```

## Novel Gameplay Experience

There are now two ways to beat the guard in the courtyard of Action Castle. Formerly, a stout branch was required to attack the guard. Now, the guard can be beaten by talking to the guard and insulting him. If the sentiment in the user's comment to the guard is negative, the guard becomes distraught and abandons his post, dropping the key to the tower room where the princess is held. 

### Example 2

The following example demonstrates how a conversation may be begun and ended with the guard. In the event of a user comment with a positive sentiment, the game keeps seeking further input. In the event of a negative comment, the guard is beaten as described above.

```
You are in the courtyard of ACTION CASTLE.
Exits: West, East, Up, Down
You see: 
a guard carrying a sword and a key
	 talk to guard
	 hit guard with branch
> talk to guard
You start talking to the guard.
Type 'STOP' to end the conversation.
>> I enjoyed my stay tremendously; what incredible service!
Type 'STOP' to end the conversation.
>> STOP
> talk to guard
You start talking to the guard.
Type 'STOP' to end the conversation.
>> You're a despicable excuse for a guard; it's a wonder you were hired.
The guard loses the will to keep doing his job.
He slumps over, with his head held in his hands.
There is a key next to him!
> look
You are in the courtyard of ACTION CASTLE.
Exits: West, East, Up, Down
You see: 
a morose looking guard is sitting on the floor
a key
> exit
I'm not sure what you want to do.
THE GAME HAS ENDED.
```
