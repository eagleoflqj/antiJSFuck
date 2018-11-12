import math
import re
from urllib import parse

defalut_date='Mon Nov 12 2018 15:54:05 GMT+0800'
class Node():
	def __init__(self,kind,value,raw):
		self.kind=kind
		self.value=value
		self.raw=raw
	def __str__(self):
		return f'Node {self.kind} {self.value}'
class JSObject():
	def __init__(self,kind,value=None):
		self.kind=kind
		self.value=value
	def __str__(self):
		return f'JSObject {self.kind} {self.value}'
class JSCode():
	def __init__(self,code):
		self.code=code
	def __str__(self):
		return f'JSCode {self.code}'
def bool2number(b):
	if b is True:
		return 1
	if b is False:
		return 0
	return b
def array2string(a):
	# if len(a)==0:
	# 	return ''
	return ','.join(o2string(x) for x in a)
def bool2string(b):
	if b is True:
		return 'true'
	if b is False:
		return 'false'
def numberToString(n,b):
	if b<2 or b>36:
		raise Exception()
	series='0123456789abcdefghijklmnopqrstuvwxyz'
	result=''
	while True:
		q,r=divmod(n,b)
		result=series[r]+result
		if q==0:
			break
		n=q
	return result
def o2string(o):
	if o.kind=='string':
		return o.value
	if o.kind=='number':
		if math.isnan(o.value):
			return 'NaN'
		if o.value==math.inf:
			return 'Infinity'
		return str(o.value)
	if o.kind=='array':
		return array2string(o.value)
	if o.kind=='bool':
		return bool2string(o.value)
	if o.kind=='undefined':
		return 'undefined'
	if o.kind=='function':
		if o.value in ('filter','String','Array','Boolean','RegExp','Number','Function'):
			return 'function '+o.value+'() { [native code] }'
	if o.kind=='object' and o.value=='this':
		return '[object Window]'
	if o.kind=='date':
		return defalut_date
	raise NotImplementedError(f'{o} to String failed')
# a+b
def add(a,b):
	if a is None:
		return b
	if a.kind=='string' or b.kind=='string':
		return JSObject('string',o2string(a)+o2string(b))
	if a.kind in ('number','bool') and b.kind=='undefined' or a.kind=='undefined' and b.kind in ('number','bool'):
		return JSObject('number',math.nan)
	if a.kind=='number' and b.kind=='number':
		return JSObject('number',a.value+b.value)
	if a.kind=='bool' and b.kind in ('bool','number') or a.kind=='number' and b.kind=='bool':
		return JSObject('number',bool2number(a.value)+bool2number(b.value))
	if a.kind in ('number','bool','undefined','array','object','date') and b.kind in('array','function') or a.kind in ('array','function') and b.kind in ('number','bool','undefined','array','object','date'):
		return JSObject('string',o2string(a)+o2string(b))
	raise NotImplementedError(f'{a} + {b} failed')
# !
def reverse(o:JSObject):
	if o.kind=='array':#![1]=false
		return JSObject('bool',False)
	if o.kind=='bool':#!false=true
		return JSObject('bool',not o.value)
	if o.kind=='number':
		if o.value==0 or math.isnan(o.value):#!0=true,!NaN=true
			return JSObject('bool',True)
		return JSObject('bool',False)#!1=false
	raise NotImplementedError(f'! {o} failed')
def call(a,b):
	if a is None:
		return b
	if a.kind=='bool' and b.kind=='array' and b.value[0].kind=='string' and b.value[0].value=='constructor':
		return JSObject('function','Boolean')
	if a.kind=='number' and b.kind=='array' and b.value[0].kind=='string' and b.value[0].value=='constructor':
		return JSObject('function','Number')
	if a.kind=='array'and b.kind=='array':
		if b.value[0].kind=='array':
			return JSObject('undefined')
		if b.value[0].kind=='string':
			if b.value[0].value=='filter':
				return JSObject('function','filter')
			if b.value[0].value=='constructor':
				return JSObject('function','Array')
			if b.value[0].value=='concat':
				return JSObject('function',('concat',a))
	if a.kind=='string' and b.kind=='array':
		if b.value[0].kind == 'number' or b.value[0].kind=='string' and re.match(r'\d+',b.value[0].value):
			return JSObject('string',a.value[int(b.value[0].value)])
		if b.value[0].kind == 'string':
			if b.value[0].value=='constructor':
				return JSObject('function','String')
			if b.value[0].value in ('italics','fontcolor'):
				return JSObject('function',(b.value[0].value,a.value))
	if a.kind=='function':
		if a.value=='escape':
			return JSObject('string',parse.quote(b.value))
		if a.value=='unescape':
			return JSObject('string',parse.unquote(b.value))
		if a.value=='Function' and b.kind=='string':
			m=re.match(r'return(\s\S.*|\/\S+)',b.value)
			if m:
				return_value=m.group(1).strip()
				return JSObject('function',('return',return_value))
			return JSObject('function',b)
		if a.value=='Date':
			return JSObject('string',defalut_date)#I'm too lazy to generate a real time
		if isinstance(a.value,tuple):
			if a.value[0]=='return':
				if a.value[1] in ('escape','unescape','italics','Date'):
					return JSObject('function',a.value[1])
				if a.value[1]=='this':
					return JSObject('object','this')
				if a.value[1][0]=='/':
					return JSObject('regexp',a.value[1][1:-1])
				m=re.match(r'new\s+Date\((\d+)\)',a.value[1])
				if m:
					return(JSObject('date',int(m.group(1))))
			if a.value[0]=='italics':
				return JSObject('string',f'<i>{a.value[1]}</i>')
			if a.value[0]=='fontcolor':
				return JSObject('string',f'<font color="undefined">{a.value[1]}</font>')
			if a.value[0]=='concat' and b.kind=='array':
				return JSObject('array',a.value[1].value+b.value)
		if b is None:
			return JSCode(a.value.value)
		if b.kind=='array' and b.value[0].value=='constructor':
			return JSObject('function','Function')
		if isinstance(a.value,tuple) and a.value[0]=='toString':
			return JSObject('string',numberToString(a.value[1],int(b.value)))
	if a.kind=='number' and b.kind=='array' and b.value[0].kind=='string' and b.value[0].value=='toString':
		return JSObject('function',('toString',a.value))
	if a.kind=='regexp' and b.kind=='array' and b.value[0].kind=='string' and b.value[0].value=='constructor':
		return JSObject('function','RegExp')
	raise NotImplementedError(f'{a} call {b} failed')
# +
def positive(o):
	if o.kind=='array':
		if len(o.value)==0:#+[]=0
			return JSObject('number',0)
		if o.value[0].kind=='number':#+[1]=1
			return JSObject('number',o.value[0].value)
		if o.value[0].kind=='bool':#+[true]=NaN
			return JSObject('number',math.nan)
	if o.kind=='bool':#+false=0
		return JSObject('number',bool2number(o.value))
	if o.kind=='string':#+"1"=1
		try:
			value=int(o.value)
		except:
			value=float(o.value)
		return JSObject('number',value)
	raise NotImplementedError(f'+ {o} failed')
def evaluate_term(o):
	if o[0]=='!':
		return reverse(evaluate_term(o[1:]))
	if o[0]=='+':
		return positive(evaluate_term(o[1:]))
	result=None
	for item in o:
		result=call(result,evaluate(item))
	return result
def evaluate_list(o):
	if len(o)==0:
		return None
	start=0
	now=0
	terms=[]
	while now<len(o):
		if o[now]=='#':
			terms.append(evaluate_term(o[start:now]))
			start=now+1
			now=start
		now+=1
	terms.append(evaluate_term(o[start:now]))
	result=None
	for term in terms:
		result=add(result,term)
	return result
def evaluate(o):
	if isinstance(o,list):
		return evaluate_list(o)
	if not isinstance(o,Node):
		raise Exception()
	if o.kind=='[':
		value=evaluate(o.value)
		return JSObject('array',[value] if value else [])
	if o.kind=='(':
		return evaluate(o.value)
def tostr(o,depth=0):
	s=str(depth)+' '
	if isinstance(o,list):
		s+='list\n'
		for x in o:
			s+=tostr(x,depth+1)+'\n'
		return s.strip()
	if isinstance(o,Node):
		s+='Node '+o.kind
		if isinstance(o.value,list):
			s+='\n'+tostr(o.value,depth+1)
	else:
		s+=o
	return s
def fight(jsfuck_code):
	# build simple AST
	stack=[]
	aux=[]
	pairs={']':'[',')':'('}
	for index,c in enumerate(jsfuck_code):
		if c in ('[','(','!'):
			stack.append(c)
			aux.append(index)
		elif c in pairs:
			left=pairs[c]
			i=len(stack)-1
			while stack[i]!=left:
				i-=1
			node=Node(left,stack[i+1:],jsfuck_code[aux[i]:index+1])
			stack=stack[:i]
			stack.append(node)
			aux=aux[:i]
			aux.append(None)
		elif c=='+':
			if len(stack)>0 and isinstance(stack[-1],Node):
				stack.append('#')
				aux.append(None)
			else:
				stack.append('+')
				aux.append(None)
		else:
			raise Exception(f'not jsfuck character {c}')
	return evaluate(stack).code
