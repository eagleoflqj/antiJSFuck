import html
import math
import re
import time
from urllib import parse

default_date = 'Mon Nov 12 2018 15:54:05 GMT+0800'


def date(millisecond):
	weekday, month, day, tm, year = time.ctime(millisecond/1000).split()
	if int(day) < 10:
		day = '0'+day
	return ' '.join((weekday, month, day, year, tm, 'GMT+0800'))


class Node():
	def __init__(self, kind, value, raw):
		self.kind = kind
		self.value = value
		self.raw = raw

	def __str__(self):
		return f'Node {self.kind} {self.value}'


class JSObject():
	def __init__(self, kind, value=None):
		self.kind = kind
		self.value = value

	def __str__(self):
		if isinstance(self.value, list):
			value = '['+','.join(str(x) for x in self.value)+']'
		elif isinstance(self.value, tuple):
			value = '('+','.join(str(x) for x in self.value)+')'
		else:
			value = self.value
		return f'JSObject {self.kind} {value}'


class JSCode():
	def __init__(self, code):
		self.code = code

	def __str__(self):
		return f'JSCode {self.code}'


def bool2number(b):
	if b is True:
		return 1
	if b is False:
		return 0
	return b


def array2string(a):
	return ','.join(o2string(x) for x in a)


def bool2string(b):
	if b is True:
		return 'true'
	if b is False:
		return 'false'


def numberToString(n, b):
	if b < 2 or b > 36:
		raise Exception()
	series = '0123456789abcdefghijklmnopqrstuvwxyz'
	result = ''
	while True:
		q, r = divmod(n, b)
		result = series[r]+result
		if q == 0:
			break
		n = q
	return result


def int_like(o: JSObject):
	if o.kind == 'Number' and isinstance(o.value, int) or o.kind == 'String' and re.match(r'[\+\-]?\d+', o.value):
		return True
	return False


def o2string(o: JSObject):
	if o.kind == 'String':
		return o.value
	if o.kind == 'Number':
		if math.isnan(o.value):
			return 'NaN'
		if o.value == math.inf:
			return 'Infinity'
		return str(o.value)
	if o.kind == 'Array':
		return array2string(o.value)
	if o.kind == 'Boolean':
		return bool2string(o.value)
	if o.kind == 'undefined':
		return 'undefined'
	if o.kind == 'Function':
		if o.value in ('filter', 'String', 'Array', 'Boolean', 'RegExp', 'Number', 'Function', 'fill'):
			return 'function '+o.value+'() { [native code] }'
	if o.kind == 'Object':
		if o.value == 'this':
			return '[object Window]'
		if o.value == 'Array Iterator':
			return '[object Array Iterator]'
		if o.value == '{}':
			return '[object Object]'
	if o.kind == 'Date':
		return date(o.value)
	if o.kind == 'RegExp':
		return o.value
	raise NotImplementedError(f'{o} to String failed')
# a+b


def add(a, b):
	to_stringer = ('Array', 'Function', 'Object', 'String', 'RegExp', 'Date')
	if a is None:
		return b
	if a.kind in to_stringer or b.kind in to_stringer:
		return JSObject('String', o2string(a)+o2string(b))
	if a.kind in ('Number', 'Boolean') and b.kind == 'undefined' or a.kind == 'undefined' and b.kind in ('Number', 'Boolean'):
		return JSObject('Number', math.nan)
	if a.kind == 'Number' and b.kind == 'Number':
		return JSObject('Number', a.value+b.value)
	if a.kind == 'Boolean' and b.kind in ('Boolean', 'Number') or a.kind == 'Number' and b.kind == 'Boolean':
		return JSObject('Number', bool2number(a.value)+bool2number(b.value))
	raise NotImplementedError(f'{a} + {b} failed')
# !


def reverse(o: JSObject):
	if o.kind == 'Array':  # ![1]=false
		return JSObject('Boolean', False)
	if o.kind == 'Boolean':  # !false=true
		return JSObject('Boolean', not o.value)
	if o.kind == 'Number':
		if o.value == 0 or math.isnan(o.value):  # !0=true,!NaN=true
			return JSObject('Boolean', True)
		return JSObject('Boolean', False)  # !1=false
	raise NotImplementedError(f'! {o} failed')


def call(a, b):
	if a is None:
		return b
	if isinstance(b, JSObject) and b.kind == 'Array' and b.value[0].kind == 'String':
		if b.value[0].value == 'constructor':
			return JSObject('Function', a.kind)
	if a.kind == 'Array'and b.kind == 'Array':
		if b.value[0].kind == 'Array':
			return JSObject('undefined')
		if b.value[0].kind == 'String':
			if b.value[0].value == 'filter':
				return JSObject('Function', 'filter')
			if b.value[0].value == 'concat':
				return JSObject('Function', ('concat', a))
			if b.value[0].value == 'fill':
				return JSObject('Function', 'fill')
			if b.value[0].value == 'entries':
				return JSObject('Function', 'entries')
			if b.value[0].value == 'slice':
				return JSObject('Function', ('slice', a))
	if a.kind == 'String':
		if b.kind == 'Array':
			if int_like(b.value[0]):
				return JSObject('String', a.value[int(b.value[0].value)])
			if b.value[0].kind == 'String':
				if b.value[0].value in ('italics', 'fontcolor', 'link', 'slice'):
					return JSObject('Function', (b.value[0].value, a))
		if b.kind == 'Function' and \
				isinstance(b.value, tuple) and b.value[0] == 'slice' and b.value[1].kind == 'Array':
			return JSObject('Array', [JSObject('String', x) for x in a.value])
	if a.kind == 'Function':
		# f()
		if a.value == 'escape':
			return JSObject('String', parse.quote(o2string(b)))
		if a.value == 'unescape':
			return JSObject('String', parse.unquote(b.value))
		if a.value == 'Function':
			if b is None:
				return JSObject('Function', JSObject('String', ''))
			if b.kind == 'String':
				m = re.match(r'return(\s\S.*|[\/\{]\S+)', b.value)
				if m:
					return_value = m.group(1).strip()
					return JSObject('Function', ('return', return_value))
				return JSObject('Function', b)
		if a.value == 'Array':
			if b is None:
				return JSObject('Array', [])
			if b.kind == 'String':
				return JSObject('Array', [b])
		# potential bug: not distinguish f[] and f([])
		if a.value == 'String' and b.kind == 'Array' and b.value[0].kind == 'String':
			if b.value[0].value == 'fromCharCode':
				return JSObject('Function', 'fromCharCode')
			if b.value[0].value == 'name':
				return JSObject('String', 'String')
		if a.value == 'Date':
			# I'm too lazy to generate a real time
			return JSObject('String', default_date)
		if a.value == 'RegExp':
			return JSObject('RegExp', '/(?:)/')
		if a.value == 'fromCharCode':
			return JSObject('String', chr(int(b.value)))
		if a.value == 'eval' and b.kind == 'String':
			return JSCode(b.value)
		if a.value == 'entries':
			return JSObject('Object', 'Array Iterator')
		if isinstance(a.value, tuple):
			if a.value[0] == 'return':
				return_value = a.value[1]
				if return_value in ('escape', 'unescape', 'italics', 'Date', 'eval'):
					return JSObject('Function', return_value)
				if return_value == 'this':
					return JSObject('Object', 'this')
				if return_value[0] == '/':
					return JSObject('RegExp', return_value)
				if return_value[0] == '{':
					return JSObject('Object', return_value)
				m = re.match(r'new\s+Date\((\d+)\)', return_value)
				if m:
					return JSObject('Date', int(m.group(1)))
			if a.value[0] == 'italics':
				return JSObject('String', f'<i>{a.value[1].value}</i>')
			if a.value[0] == 'fontcolor':
				return JSObject('String', f'<font color="undefined">{a.value[1].value}</font>')
			if a.value[0] == 'concat' and b.kind == 'Array':
				return JSObject('Array', a.value[1].value+b.value)
			if a.value[0] == 'toString':
				return JSObject('String', numberToString(a.value[1], int(b.value)))
			if a.value[0] == 'link':
				return JSObject('String', f'<a href="{html.escape(b.value)}">{a.value[1].value}</a>')
			if a.value[0] == 'slice' and int_like(b):
				return JSObject('String', a.value[1].value[int(b.value)])
			if a.value[0] == 'call':
				return call(b, a.value[1])
		if b is None and isinstance(a.value, JSObject) and a.value.kind == 'String':
			return JSCode(a.value.value)
		# f.g
		if isinstance(b, JSObject) and b.kind == 'Array':
			if b.value[0].value == 'call':
				return JSObject('Function', ('call', a))
	if a.kind == 'Number' and b.kind == 'Array' and b.value[0].kind == 'String' and b.value[0].value == 'toString':
		return JSObject('Function', ('toString', a.value))
	raise NotImplementedError(f'{a} call {b} failed')
# +


def positive(o):
	if o.kind == 'Array':
		if len(o.value) == 0:  # +[]=0
			return JSObject('Number', 0)
		if o.value[0].kind == 'Number':  # +[1]=1
			return JSObject('Number', o.value[0].value)
		if o.value[0].kind == 'Boolean':  # +[true]=NaN
			return JSObject('Number', math.nan)
	if o.kind == 'Boolean':  # +false=0
		return JSObject('Number', bool2number(o.value))
	if o.kind == 'String':  # +"1"=1
		try:
			value = int(o.value)
		except:
			value = float(o.value)
		return JSObject('Number', value)
	raise NotImplementedError(f'+ {o} failed')


def evaluate_term(o):
	if o[0] == '!':
		return reverse(evaluate_term(o[1:]))
	if o[0] == '+':
		return positive(evaluate_term(o[1:]))
	result = None
	for item in o:
		result = call(result, evaluate(item))
	return result


def evaluate_list(o):
	if len(o) == 0:
		return None
	start = 0
	now = 0
	terms = []
	while now < len(o):
		if o[now] == '#':
			terms.append(evaluate_term(o[start:now]))
			start = now+1
			now = start
		now += 1
	terms.append(evaluate_term(o[start:now]))
	result = None
	for term in terms:
		result = add(result, term)
	return result


def evaluate(o):
	if isinstance(o, list):
		return evaluate_list(o)
	if not isinstance(o, Node):
		raise Exception()
	if o.kind == '[':
		value = evaluate(o.value)
		return JSObject('Array', [value] if value else [])
	if o.kind == '(':
		return evaluate(o.value)


def fight(jsfuck_code):
	# build simple AST
	stack = []
	aux = []
	pairs = {']': '[', ')': '('}
	for index, c in enumerate(jsfuck_code):
		if c in ('[', '(', '!'):
			stack.append(c)
			aux.append(index)
		elif c in pairs:
			left = pairs[c]
			i = len(stack)-1
			while stack[i] != left:
				i -= 1
			node = Node(left, stack[i+1:], jsfuck_code[aux[i]:index+1])
			stack = stack[:i]
			stack.append(node)
			aux = aux[:i]
			aux.append(None)
		elif c == '+':
			if len(stack) > 0 and isinstance(stack[-1], Node):
				stack.append('#')
				aux.append(None)
			else:
				stack.append('+')
				aux.append(None)
		else:
			raise Exception(f'not jsfuck character {c}')
	return evaluate(stack).code
