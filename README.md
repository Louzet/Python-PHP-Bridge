This is a Python module for running PHP programs. It makes PHP functions, classes, objects, constants and variables available to be used just like regular Python versions.

You can call functions:
```
>>> from phpbridge import php
>>> php.array_flip(["foo", "bar"])
{'foo': 0, 'bar': 1}
>>> php.echo("foo\n")
foo
>>> php.getimagesize("http://php.net/images/logos/new-php-logo.png")
{'0': 200, '1': 106, '2': 3, '3': 'width="200" height="106"', 'bits': 8, 'mime': 'image/png'}
```

You can create and use objects:
```
>>> php.DateTime
<PHP class 'DateTime'>
>>> date = php.DateTime()
>>> print(date)
<DateTime Object
(
    [date] => 2018-04-27 17:01:45.099376
    [timezone_type] => 3
    [timezone] => Europe/Berlin
)>
>>> date.getOffset()
7200
>>> php.ArrayAccess
<PHP interface 'ArrayAccess'>
>>> issubclass(php.ArrayObject, php.ArrayAccess)
True
```

You can use keyword arguments, even though PHP doesn't support them:
```
>>> date.setDate(year=1900, day=20, month=10)
<DateTime Object
(
    [date] => 1900-10-20 14:26:19.146087
    [timezone_type] => 3
    [timezone] => Europe/Berlin
)>
```

You can loop over iterators and traversables:
```
>>> for path, file in php.RecursiveIteratorIterator(php.RecursiveDirectoryIterator('.git/logs')):
...     print("{}: {}".format(path, file.getSize()))
...
.git/logs/.: 16
.git/logs/..: 144
.git/logs/HEAD: 2461
[...]
```

You can get help:
```
>>> help(php.echo)
Help on function echo:

echo(arg1, *rest)
    Output one or more strings.

    @param mixed $arg1
    @param mixed ...$rest

    @return void
>>> help(php._.blyxxyz.PythonServer._.NonFunctionProxy)
Help on class blyxxyz\PythonServer\NonFunctionProxy:

class blyxxyz\PythonServer\NonFunctionProxy(phpbridge.objects.PHPObject)
 |  Provide function-like language constructs as static methods.
 |
 |  `isset` and `empty` are not provided because it's impossible for a real
 |  function to check whether its argument is defined.
 |
 |  Method resolution order:
 |      blyxxyz\PythonServer\NonFunctionProxy
 |      phpbridge.objects.PHPObject
 |      builtins.object
 |
 |  Class methods defined here:
 |
 |  array(val) -> dict from phpbridge.objects.PHPClass
 |      Cast a value to an array
 |
 |      @param mixed $val
 |
 |      @return array
[...]
```

You can index, and get lengths:
```
>>> arr = php.ArrayObject(['foo', 'bar', 'baz'])
>>> arr[10] = 'foobar'
>>> len(arr)
4
```

You can work with PHP's exceptions:
```
>>> try:
...     php.get_resource_type(3)
... except php.TypeError as e:
...     print(e.getMessage())
...
get_resource_type() expects parameter 1 to be resource, integer given
```

Some current features:
  * Using PHP functions
    * Keyword arguments are supported and translated based on the signature
    * Docblocks are also converted, so `help` is informative
  * Using PHP classes like Python classes
    * Methods and constants are defined right away based on the PHP class
    * Docblocks are treated like docstrings, so `help` works and is informative
    * The original inheritance structure is copied
    * Default properties become Python properties with documentation
    * Other properties are accessed on the fly as a fallback for attribute access
  * Creating and using objects
  * Getting and setting constants
  * Getting and setting global variables
  * Translating exceptions so they can be treated as both Python exceptions and PHP objects
  * Walking through namespaces like modules
  * Tab completion in the interpreter

Caveats:
  * The connection between PHP and Python is somewhat fragile, if PHP prints something to stderr, it's lost
  * Returned PHP objects are never garbage collected
  * You can only pass basic Python objects into PHP

Namespaces can be accessed by using a leading and trailing underscore on the namespace. For example, the class `PhpParser\Node\Name` becomes `php._.PHPParser.Node._.Name`. This avoids conflict with the class named `PhpParser\Node`, which can be accessed as `php._.PHPParser._.Node`.

In PHP, different kinds of things may use the same name. If there's a constant `foo` and a function `foo`, use `php.fun.foo()` rather than `php.foo()` so the bridge doesn't have to guess. There's
  * `php.cls` for classes
  * `php.const` for constants
  * `php.fun` for functions
  * `php.globals` for globals

They also support setting constants and global variables:
```
>>> php.globals.foo = 'bar'
>>> php.const['baz'] = 'foobar'
>>> php.eval("""
... global $foo;
... return [$foo, baz];
... """)
['bar', 'foobar']
```

The bridge works by piping JSON between the Python process and a PHP process.

The only dependencies are PHP 7.0+, Python 3.5+, ext-json and ext-reflection. Composer can be used to install development tools and set up autoloading, but it's not required.
