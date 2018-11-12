import string

import execjs

from antijsfuck import fight

with open('jsfuck.js','r') as f:
	jsfuck_code=f.read()
context=execjs.get().compile(jsfuck_code)
print('Testing printable ascii characters:')
for c in string.printable:
	fucked=context.call('jsfuck',c,1)
	if c==fight(fucked):
		print(ord(c),c,'passed')
	else:
		print(ord(c),c,'failed')
