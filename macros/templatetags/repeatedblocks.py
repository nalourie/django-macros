# the following file was written/built by Nicholas Lourie,
# while working for kozbox, llc. http://kozbox.com

""" repeatedblocks.py, part of django-macros, allows for easy
and explicit repetition of block tags in django templates.
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
        raise template.TemplateSyntaxError(
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
        raise template.TemplateSyntaxError(
            '{0} tag takes only one argument'.format(
                token.contents.split()[0]))
    # try to fetch the stored block
    try:
        block_node = parser._repeated_blocks[block_name]
    except (AttributeError, KeyError):
        raise template.TemplateSyntaxError(
            "No repeated block {0} tag was found before the {1} tag".format(
                block_name, tag_name))
    # return the block to be repeated
    return block_node
