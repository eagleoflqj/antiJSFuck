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
	if o.kind == 'number' and isinstance(o.value, int) or o.kind == 'string' and re.match(r'[\+\-]?\d+', o.value):
		return True
	return False


def o2string(o: JSObject):
	if o.kind == 'string':
		return o.value
	if o.kind == 'number':
		if math.isnan(o.value):
			return 'NaN'
		if o.value == math.inf:
			return 'Infinity'
		return str(o.value)
	if o.kind == 'array':
		return array2string(o.value)
	if o.kind == 'bool':
		return bool2string(o.value)
	if o.kind == 'undefined':
		return 'undefined'
	if o.kind == 'function':
		if o.value in ('filter', 'String', 'Array', 'Boolean', 'RegExp', 'Number', 'Function', 'fill'):
			return 'function '+o.value+'() { [native code] }'
	if o.kind == 'object':
		if o.value == 'this':
			return '[object Window]'
		if o.value == 'Array Iterator':
			return '[object Array Iterator]'
		if o.value == '{}':
			return '[object Object]'
	if o.kind == 'date':
		return date(o.value)
	if o.kind == 'regexp':
		return o.value
	raise NotImplementedError(f'{o} to String failed')
# a+b


def add(a, b):
	to_stringer = ('array', 'function', 'object', 'string')
	if a is None:
		return b
	if a.kind in to_stringer or b.kind in to_stringer:
		return JSObject('string', o2string(a)+o2string(b))
	if a.kind in ('number', 'bool') and b.kind == 'undefined' or a.kind == 'undefined' and b.kind in ('number', 'bool'):
		return JSObject('number', math.nan)
	if a.kind == 'number' and b.kind == 'number':
		return JSObject('number', a.value+b.value)
	if a.kind == 'bool' and b.kind in ('bool', 'number') or a.kind == 'number' and b.kind == 'bool':
		return JSObject('number', bool2number(a.value)+bool2number(b.value))
	raise NotImplementedError(f'{a} + {b} failed')
# !


def reverse(o: JSObject):
	if o.kind == 'array':  # ![1]=false
		return JSObject('bool', False)
	if o.kind == 'bool':  # !false=true
		return JSObject('bool', not o.value)
	if o.kind == 'number':
		if o.value == 0 or math.isnan(o.value):  # !0=true,!NaN=true
			return JSObject('bool', True)
		return JSObject('bool', False)  # !1=false
	raise NotImplementedError(f'! {o} failed')


def call(a, b):
	if a is None:
		return b
	if a.kind == 'bool' and b.kind == 'array' and b.value[0].kind == 'string' and b.value[0].value == 'constructor':
		return JSObject('function', 'Boolean')
	if a.kind == 'number' and b.kind == 'array' and b.value[0].kind == 'string' and b.value[0].value == 'constructor':
		return JSObject('function', 'Number')
	if a.kind == 'array'and b.kind == 'array':
		if b.value[0].kind == 'array':
			return JSObject('undefined')
		if b.value[0].kind == 'string':
			if b.value[0].value == 'filter':
				return JSObject('function', 'filter')
			if b.value[0].value == 'constructor':
				return JSObject('function', 'Array')
			if b.value[0].value == 'concat':
				return JSObject('function', ('concat', a))
			if b.value[0].value == 'fill':
				return JSObject('function', 'fill')
			if b.value[0].value == 'entries':
				return JSObject('function', 'entries')
			if b.value[0].value == 'slice':
				return JSObject('function', ('slice', a))
	if a.kind == 'string':
		if b.kind == 'array':
			if int_like(b.value[0]):
				return JSObject('string', a.value[int(b.value[0].value)])
			if b.value[0].kind == 'string':
				if b.value[0].value == 'constructor':
					return JSObject('function', 'String')
				if b.value[0].value in ('italics', 'fontcolor', 'link', 'slice'):
					return JSObject('function', (b.value[0].value, a))
		if b.kind == 'function' and \
				isinstance(b.value, tuple) and b.value[0] == 'slice' and b.value[1].kind == 'array':
			return JSObject('array', [JSObject('string', x) for x in a.value])
	if a.kind == 'function':
		# f()
		if a.value == 'escape':
			return JSObject('string', parse.quote(o2string(b)))
		if a.value == 'unescape':
			return JSObject('string', parse.unquote(b.value))
		if a.value == 'Function':
			if b is None:
				return JSObject('function', JSObject('string', ''))
			if b.kind == 'string':
				m = re.match(r'return(\s\S.*|[\/\{]\S+)', b.value)
				if m:
					return_value = m.group(1).strip()
					return JSObject('function', ('return', return_value))
				return JSObject('function', b)
		if a.value == 'Array':
			if b is None:
				return JSObject('array', [])
			if b.kind == 'string':
				return JSObject('array', [b])
		# potential bug: not distinguish f[] and f([])
		if a.value == 'String' and b.kind == 'array' and b.value[0].kind == 'string':
			if b.value[0].value == 'fromCharCode':
				return JSObject('function', 'fromCharCode')
			if b.value[0].value == 'name':
				return JSObject('string', 'String')
		if a.value == 'Date':
			# I'm too lazy to generate a real time
			return JSObject('string', default_date)
		if a.value == 'RegExp':
			return JSObject('regexp', '/(?:)/')
		if a.value == 'fromCharCode':
			return JSObject('string', chr(int(b.value)))
		if a.value == 'eval' and b.kind == 'string':
			return JSCode(b.value)
		if a.value == 'entries':
			return JSObject('object', 'Array Iterator')
		if isinstance(a.value, tuple):
			if a.value[0] == 'return':
				return_value = a.value[1]
				if return_value in ('escape', 'unescape', 'italics', 'Date', 'eval'):
					return JSObject('function', return_value)
				if return_value == 'this':
					return JSObject('object', 'this')
				if return_value[0] == '/':
					return JSObject('regexp', return_value)
				if return_value[0] == '{':
					return JSObject('object', return_value)
				m = re.match(r'new\s+Date\((\d+)\)', return_value)
				if m:
					return JSObject('date', int(m.group(1)))
			if a.value[0] == 'italics':
				return JSObject('string', f'<i>{a.value[1].value}</i>')
			if a.value[0] == 'fontcolor':
				return JSObject('string', f'<font color="undefined">{a.value[1].value}</font>')
			if a.value[0] == 'concat' and b.kind == 'array':
				return JSObject('array', a.value[1].value+b.value)
			if a.value[0] == 'toString':
				return JSObject('string', numberToString(a.value[1], int(b.value)))
			if a.value[0] == 'link':
				return JSObject('string', f'<a href="{html.escape(b.value)}">{a.value[1].value}</a>')
			if a.value[0] == 'slice' and int_like(b):
				return JSObject('string', a.value[1].value[int(b.value)])
			if a.value[0] == 'call':
				return call(b, a.value[1])
		if b is None and isinstance(a.value, JSObject) and a.value.kind == 'string':
			return JSCode(a.value.value)
		# f.g
		if isinstance(b, JSObject) and b.kind == 'array':
			if b.value[0].value == 'constructor':
				return JSObject('function', 'Function')
			if b.value[0].value == 'call':
				return JSObject('function', ('call', a))
	if a.kind == 'number' and b.kind == 'array' and b.value[0].kind == 'string' and b.value[0].value == 'toString':
		return JSObject('function', ('toString', a.value))
	if a.kind == 'regexp' and b.kind == 'array' and b.value[0].kind == 'string' and b.value[0].value == 'constructor':
		return JSObject('function', 'RegExp')
	print(int_like(b))
	raise NotImplementedError(f'{a} call {b} failed')
# +


def positive(o):
	if o.kind == 'array':
		if len(o.value) == 0:  # +[]=0
			return JSObject('number', 0)
		if o.value[0].kind == 'number':  # +[1]=1
			return JSObject('number', o.value[0].value)
		if o.value[0].kind == 'bool':  # +[true]=NaN
			return JSObject('number', math.nan)
	if o.kind == 'bool':  # +false=0
		return JSObject('number', bool2number(o.value))
	if o.kind == 'string':  # +"1"=1
		try:
			value = int(o.value)
		except:
			value = float(o.value)
		return JSObject('number', value)
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
		return JSObject('array', [value] if value else [])
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
