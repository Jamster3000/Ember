# Ember
> This is a work in progress and is only developed occasionally at the moment. This README will be improved in later dev
Ember is a new programming language designed to be ease of use for low and high level prorammers whilst meeting and succeeding many gaps and downfalls of other programming languages

This code was built and ran on a Intel I5 Vpro on Linux Manjaro OS. And hasn't been tested on anything else as of yet.

Below is an example of what actually works as of right now
```ember
testone = -5
testtwo = 5
testthree = 50000

output(testone)
output(testtwo)
output(testthree)
```

Which when ran you'll see some similar output
```ember
Lexer output:

IDENTIFIER ASSIGNMENT NUMBER IDENTIFIER ASSIGNMENT NUMBER IDENTIFIER ASSIGNMENT NUMBER FUNCTION OPEN_PAREN IDENTIFIER CLOSE_PAREN FUNCTION OPEN_PAREN IDENTIFIER CLOSE_PAREN FUNCTION OPEN_PAREN IDENTIFIER CLOSE_PAREN 

Parser output:
AST:
Assignment
  Identifier: testone
  Value: -5
Assignment
  Identifier: testtwo
  Value: 5
Assignment
  Identifier: testthree
  Value: 50000
Function Call
  Function: output
  Argument: testone
  OUTPUT: -5
Function Call
  Function: output
  Argument: testtwo
  OUTPUT: 5
Function Call
  Function: output
  Argument: testthree
  OUTPUT: 50000
```

### Developing Emberon
To develop Emberon as in edit and run the asm code, you will need to install nasm (this was what was used to build and run it)
Running emberon code, you will only need to use the "Emberon" file as that is the interpreter.

To run the interpreter run the following command
`./emberon [filename].emb`
