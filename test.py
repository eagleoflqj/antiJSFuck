import execjs
import string
from antijsfuck import fight
with open('jsfuck.js','r') as f:
	jsfuck_code=f.read()
context=execjs.get().compile(jsfuck_code)
for c in string.printable:
	fucked=context.call('jsfuck',c,1)
	if c!=fight(fucked):
		print(c)