import string

import execjs

from antijsfuck import fight

for source in ('jsfuck','jsfuck_plus'):
	with open(f'{source}.js','r') as f:
		jsfuck_code=f.read()
	context=execjs.get().compile(jsfuck_code)
	print(f'Testing printable ASCII characters with {source}:')
	for c in string.printable:
		fucked=context.call(source,c,1,1)
		result=c+' '
		try:
			if c==fight(fucked).code:
				result+='passed'
			else:
				result+='failed'
		except:
			result+='crashed'
		print(result,f'(ASCII {ord(c)})')