x = 1

# Unary operations
+x
-x
not x
~x

# Binary operations
x + x
x - x
x * x
x / x
x // x
x % x
x ** x
x << x
x >> x
x | x
x ^ x
x & x

# Boolean operations
x and x
x or x and x

# Comparison operators
x < x
x > x
1 <= x < 3
x in (1, 2, 3)
x != 1
x >= 0
None is None

# Call expressions
(lambda y: y)(x)
(lambda y: y)(y=x)
args = (1, 2)
min(*args)
kwargs = {'x': 1, 'y': 2}
(lambda **kwargs: kwargs['x'])(**kwargs)
(lambda a, b, c: a + b + c)(1, 2, c=3)

z = 1 if True else 2
z.real

# Subscripting
args[z]
args[1:]
args[::-1]

# Comprehensions
[y+1 for y in args]
{1 for _ in kwargs}
(y+1 for y in args)
{y: y+1 for y in args}
[x+y for x in args for y in args]

# f-strings
f'Empty f-string'
f'Here is x: {x}!'
f'Three plus two is {3 + 2}'
f'Some fancily formatted number: ${126783.6457:,.2f}'
