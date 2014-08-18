# the following file was written/built by Nicholas Lourie,
# while working for kozbox, llc. http://kozbox.com

"""
Installation:

    See readme in root directory, or visit the git at
    https://github.com/nalourie/django-macros


Useage:

    At the beginning of your file include:
        {% load repeatedblocks %}
        
    When you have a block that you want to repeat, instead of
    using a block tag, use a repeated block:

        {% repeatedblock some_block name %}
            ...
            ...
            ...
        {% endblock %}

    Later, when you want to repeat that block again, simply
    include the repeat tag:

        {% repeat some_block name %}


    Thus, the following template:

        {% repeatedblock title %}Repeated Block Tags{% endblock %}

        {% repeat title %}

    Renders to:

        Repeated Block Tags

        Repeated Block Tags

    Make sure that the {% repeat ... %} tag comes after the
    {% repeatedblock ... %} ... {% endblock %} tag.

    They are fully inheritable, repeat inherited content and
    should work exactly as you'd expect a block tag to work.
"""

"""
Design Explanation:

Using a "repeatedblock" followed by "repeat" tag
structure, as opposed to just repeating normal block tags
forces developers to be more explicit about what is repeated.
Thus, it guards against the potential to remove block
tags later in development, not realize they are repeated,
and create an error later. Hence, we've chosen this design since 
it's more advantageous/pythonic in being explicit as well as dry.
"""

from django import template
from django.template.loader_tags import BlockNode, do_block
from django.conf import settings

register = template.Library()


def set_repeated_blocks(parser):
    """ helper function to initialize
    the internal variable set on the parser.
    """
    try:
        parser._repeated_blocks
    except AttributeError:
        parser._repeated_blocks = {}



@register.tag
def repeated_block(parser, token):
    try:
        tag_name, block_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntexError(
            '{0} tag takes only one argument'.format(
                token.contents.split()[0]))
    # initialize attribute storing block contents on parser
    set_repeated_blocks(parser)
    # do_block is the internal function for creating block tags
    block_node = do_block(parser, token)
    # store block in parser's attribute
    parser._repeated_blocks[block_name] = block_node
    # return a normal block node so that it behaves exactly
    # as people would expect.
    return block_node



@register.tag
def repeat(parser, token):
    try:
        tag_name, block_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntexError(
            '{0} tag takes only one argument'.format(
                token.contents.split()[0]))
    # try to fetch the stored block
    try:
        block_node = parser._repeated_blocks[block_name]
    except (AttributeError, KeyError):
        raise ValueError(
            "No block {0} tag was found before the {1} tag".format(
                block_name, tag_name))
    # return the block to be repeated
    return block_node
