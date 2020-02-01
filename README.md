# InteractiveFictionCIS700
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
* annotations of word senses for these commands results in expanded support 12524 commands instead of the 7 in the above list
* the improved parser is built on top of the simple string-matching parser; a command is first passed through the simple parser, and if no match is found, it is then passed through the WordNet enhanced list of alternative commands; if no match is found yet again, then a semantically closest alternative command is searched for using Word2Vec embeddings of the user's command and the known set of 12524 commands (similarity between commands must exceed 0.5 for the alternative to be accepted)
