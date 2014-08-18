django-macros
=============

Macros accepting positional and keyword arguments, and repeated block tags in the django template system. Sometimes include tags just don't get the job done. Either you have repeated code that you want to keep all in the same single template, or your code needs to dynamically generate and sub in certain values. Whatever the case, if you're finding that the built in template tag just isn't working for your use case, then perhaps django-macros is for you.

visit the [github](https://github.com/nalourie/django-macros).
    

# Installation:

from the command line:

```
pip install django-macros
```

Within settings.py, add 'macros' to INSTALLED_APPS:

```
INSTALLED_APPS = (
    ...
    'macros',
    ...
)
```

# Useage:

django-macros contains two template tag libraries, one for creating macros within templates, and one for repeating block tags.

## Macros Useage

### Explained Useage

At the beginning of your file include:

```
{% load macros %}
```

When you have a section of your template you want to repeat, but don't want to have inherited or any other block tag-like functionality, define a macro as follows:

```
{% macro some_macro_name arg1 arg2 kwarg="default" %}
    {{ arg1 }} was the first argument.
    {{ arg2 }} was the second argument.

    {% if kwarg %}This is a {{ kwarg }}. {% endif %}
{% endmacro %}
```

Then when you want to use the macro, simply do:

```
{% use_macro "foo" "bar" kwarg="nondefault value" %}
```

which renders to:

```
foo was the first argument.
bar was the second argument.
This is a nondefault value.
```

Alternatively, you can save your macros in a separate file, e.g. "mymacros.html" and load it into the template with the tag `{% loadmacros "mymacros.html" %}` then use them with the `{% use_macro ... %}` tag.


All macros, including loaded ones, are local to the template file they are loaded into/defined in, and are not inherited through `{% extends ... %}` tags.

### A more in-depth useage example:

#### Macro:

```
{% macro test2args1kwarg arg1 arg2 baz="Default baz" %}
    {% firstof arg1 "default arg1" %}
    {% if arg2 %}{{ arg2 }}{% else %}default arg2{% endif %}
    {{ baz }}
{% endmacro %}
            
         
{% use_macro test2args1kwarg "foo" "bar" baz="KW" %}
<br>
{% use_macro test2args1kwarg num_pages "bar" %}
<br>
{% use_macro test2args1kwarg %}
<br>
{% use_macro test2args1kwarg "new" "foobar"|join:"," baz="diff kwarg" %}
```

#### renders as:

```
foo bar KW
77 bar Default baz
default arg1 default arg2 Default baz
new f,o,o,b,a,r diff kwarg
```

### Extended Syntax

Sometimes you might want to include data that is rendered by the template engine, or longer data containing a lot of html in a macro. For this, the syntax of plugging arguments directly into the tag doesn't really work, so instead of `{% use_macro some_macro_name "arg" kwarg_name="value" %}`, use the syntax below:

```
{% macro_block some_macro_name %}
    {% macro_arg %}
        arg
    {% endmacro_arg %}
    
    {% macro_kwarg kwarg_name %}
        value
    {% endmacro_kwarg %}
{% endmacro_block %}
```

Note that with this syntax you no longer have to quote strings/arguments.

## Repeated Blocks Useage:

At the beginning of your file include:
        
```        
{% load repeatedblocks %}
```

When you have a block that you want to repeat, instead of using a block tag, use a repeated block:

```
{% repeatedblock some_block name %}
    ...
    ...
    ...
{% endblock %}
```

Later, when you want to repeat that block again, simply include the repeat tag:

```
{% repeat some_block name %}
```

Thus, the following template:

```
{% repeatedblock title %}Repeated Block Tags{% endblock %}

{% repeat title %}
```

Renders to:

```
Repeated Block Tags

Repeated Block Tags
```

Make sure that the `{% repeat ... %}` tag comes **after** the `{% repeatedblock ... %} ... {% endblock %}` tag.

They are fully inheritable, repeat inherited content and should work exactly as you'd expect a block tag to work.

# Bonus Content!

## Design Explanation for repeatedblocks.py:

Using a "repeatedblock" followed by "repeat" tag structure, as opposed to just repeating normal block tags, forces developers to be more explicit about what is repeated. Thus, it guards against the potential to remove block tags later in development, not realize they are repeated, and create an error later. Hence, we've chosen this design since it's more advantageous/pythonic in being explicit as well as dry.

# Credits

The macros tags are based on snippet originally by [Michal Ludvig](http://www.logix.cz/michal), <michal@logix.cz>, later modified for args and kwargs by [Skylar Saveland](http://skyl.org).

Code was updated for django 1.6, modified, and packaged by Nicholas Lourie, while working for [kozbox, llc](http://kozbox.com). Nick also added the extended syntax to the macros.