# Based on snippet by
# Author: Michal Ludvig <michal@logix.cz>
#         http://www.logix.cz/michal
#
# modified for args and kwargs by Skylar Saveland http://skyl.org
#
# updated for django 1.6, modified, and packaged by Nicholas Lourie,
# while working for kozbox, llc. http://kozbox.com

""" Macros.py, part of django-macros, allows for creation of
macros within django templates.
"""

from re import match as regex_match
from django import template
from django.template import FilterExpression
from django.template.loader import get_template
 
register = template.Library()
 
 
def _setup_macros_dict(parser):
    """ initiates the _macros attribute on the parser
    object, allowing for storage of the macros in the parser.
    """
    ## Each macro is stored in a new attribute
    ## of the 'parser' class. That way we can access it later
    ## in the template when processing 'use_macro' tags.
    try:
        # don't overwrite the attribute if it already exists
        parser._macros
    except AttributeError:
        parser._macros = {}
 
 
class DefineMacroNode(template.Node):
    """ The node object for the tag which
    defines a macro.
    """
    def __init__(self, name, nodelist, args, kwargs):
        # the values in the kwargs dictionary are by
        # assumption instances of template.Variable.
        self.name = name
        self.nodelist = nodelist
        self.args = args
        self.kwargs = kwargs
 
    def render(self, context):
        ## empty string - {% macro %} tag has no output
        return ''
 
 
@register.tag(name="macro")
def do_macro(parser, token):
    """ the function taking the parsed tag and returning
    a DefineMacroNode object.
    """
    try:
        bits = token.split_contents()
        tag_name, macro_name, arguments = bits[0], bits[1], bits[2:]
    except IndexError:
        raise template.TemplateSyntaxError(
            "'{0}' tag requires at least one argument (macro name)".format(
            token.contents.split()[0]))
    
    # use regex's to parse the arguments into arg
    # and kwarg definitions

    # the regex for identifying python variable names is:
    ##  r'^[A-Za-z_][\w_]*$'

    # args must be proper python variable names
    ## we'll want to capture it from the regex also.
    arg_regex = r'^([A-Za-z_][\w_]*)$'

    # kwargs must be proper variable names with a
    # default value, name="value", or name=value if
    # value is a template variable (potentially with
    # filters).
    ## we'll want to capture the name and value from
    ## the regex as well.
    kwarg_regex = r'^([A-Za-z_][\w_]*)=(.+)$'
    # leave further validation to the template variable class

    args = []
    kwargs = {}
    for argument in arguments:
        arg_match = regex_match(
            arg_regex, argument)
        if arg_match:
            args.append(arg_match.groups()[0])
        else:
            kwarg_match = regex_match(
                kwarg_regex, argument)
            if kwarg_match:
                kwargs[kwarg_match.groups()[0]] = template.Variable(
                    # convert to a template variable here
                    kwarg_match.groups()[1])
            else:
                raise template.TemplateSyntaxError(
                    "Malformed arguments to the {0} tag.".format(
                        tag_name))
    
    # parse to the endmacro tag and get the contents
    nodelist = parser.parse(('endmacro', ))
    parser.delete_first_token()
 
    # store macro in parser._macros, creating attribute
    # if necessary
    _setup_macros_dict(parser)
    parser._macros[macro_name] = DefineMacroNode(
        macro_name, nodelist, args, kwargs)
    return parser._macros[macro_name]
 
 
class LoadMacrosNode(template.Node):
    """ The template tag node for loading macros from
    an external sheet.
    """
    def render(self, context):
        ## empty string - {% loadmacros %} tag does no output
        return ''
 
 
@register.tag(name="loadmacros")
def do_loadmacros(parser, token):
    """ The function taking a parsed tag and returning
    a LoadMacrosNode object, while also loading the macros
    into the page.
    """
    try:
        tag_name, filename = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "'{0}' tag requires at least one argument (macro name)".format(
            token.contents.split()[0]))
    if filename[0] in ('"', "'") and filename[-1] == filename[0]:
        filename = filename[1:-1]
    else:
        raise template.TemplateSyntaxError(
            "Malformed argument to the {0} template tag.".format(tag_name) +
            " Argument must be in quotes.")
    t = get_template(filename)
    macros = t.nodelist.get_nodes_by_type(DefineMacroNode)
    # make sure the _macros attribute dictionary is instantiated
    # on the parser, then add the macros to it.
    _setup_macros_dict(parser)
    for macro in macros:
        parser._macros[macro.name] = macro
    return LoadMacrosNode()
 
 
class UseMacroNode(template.Node):
    """ Template tag Node object for the tag which
    uses a macro.
    """
 
    def __init__(self, macro, args, kwargs):
        # all the values kwargs and the items in args
        # are by assumption template.Variable instances.
        self.macro = macro
        self.args = args
        self.kwargs = kwargs
 
    def render(self, context):

        # add all of the use_macros args into context
        for i, arg in enumerate(self.macro.args):
            try:
                template_variable = self.args[i]
                context[arg] = template_variable.resolve(context)
            except IndexError:
                context[arg] = ""

        # add all of use_macros kwargs into context
        for name, default in self.macro.kwargs.iteritems():
            if name in self.kwargs:
                context[name] = self.kwargs[name].resolve(context)
            else:
                context[name] = default.resolve(context)

        # return the nodelist rendered in the adjusted context
        return self.macro.nodelist.render(context)
 
 
@register.tag(name="use_macro")
def do_usemacro(parser, token):
    """ The function taking a parsed template tag
    and returning a UseMacroNode.
    """
    try:
        bits = token.split_contents()
        tag_name, macro_name, values = bits[0], bits[1], bits[2:]
    except IndexError:
        raise template.TemplateSyntaxError(
            "{0} tag requires at least one argument (macro name)".format(
                token.contents.split()[0]))
    try:
        macro = parser._macros[macro_name]
    except (AttributeError, KeyError):
        raise template.TemplateSyntaxError(
            "Macro '{0}' is not defined previously to the {1} tag".format(macro_name, tag_name))

    args = []
    kwargs = {}

    # leaving most validation up to the template.Variable
    # class, but use regex here so that validation could
    # be added in future if necessary.
    kwarg_regex = r'^([A-Za-z_][\w_]*)=(.+)$'
    arg_regex = r'^(.+)$'
    for value in values:
        # must check against the kwarg regex first
        # because the arg regex matches everything!
        kwarg_match = regex_match(
            kwarg_regex, value)
        if kwarg_match:
            kwargs[kwarg_match.groups()[0]] = template.Variable(
                # convert to a template variable here
                kwarg_match.groups()[1])
        else:
            arg_match = regex_match(
                arg_regex, value)
            if arg_match:
                args.append(template.Variable(arg_match.groups()[0]))
            else:
                raise template.TemplateSyntaxError(
                    "Malformed arguments to the {0} tag.".format(
                        tag_name))
    macro.parser = parser
    return UseMacroNode(macro, args, kwargs)


class MacroBlockNode(template.Node):
    """ Template node object for the extended
    syntax macro useage.
    """
    def __init__(self, macro, nodelist, args, kwargs):
        # items in the args list and values in the kwargs
        # dict are assumed to be MacroArgNodes and
        # MacroKwargNodes respectively.
        self.macro = macro
        self.nodelist = nodelist
        self.args = args
        self.kwargs = kwargs

    def render(self, context):
        # take the macro_block's args, and sub them
        # into the context for macro's args.
        for i, arg in enumerate(self.macro.args):
            try:
                context[arg] = self.args[i].nodelist.render(context)
            except IndexError:
                # have missing args fail silently as usual
                context[arg] = ""

        # take macro_block's kwargs, and sub them
        # into the context for macro's kwargs.
        for name, default in self.macro.kwargs.iteritems():
            try:
                # add the rendered contents of the tag to the context
                context[name] = self.kwargs[name].nodelist.render(context)
            except KeyError:
                # default value is a template variable that needs to be
                # resolved in the context.
                context[name] = default.resolve(context)

        return self.macro.nodelist.render(context)


@register.tag(name="macro_block")
def do_macro_block(parser, token):
    """ Function taking parsed template tag
    to a MacroBlockNode.
    """
    try:
        tag_name, macro_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "{0} tag requires exactly one argument,".format(
                tag_name) + " a macro's name")
    # could add extra validation on the macro_name tag
    # here, but probably don't need to since we're checking
    # if there's a macro by that name anyway.
    try:
        # see if the macro is in the context.
        macro = parser._macros[macro_name]
    except (AttributeError, KeyError):
        raise template.TemplateSyntaxError(
            "Macro '{0}' is not defined".format(macro))
    # get the arg and kwarg nodes from the nodelist
    nodelist = parser.parse(('endmacro_block', ))
    parser.delete_first_token()

    args = []
    kwargs = {}
    # Loop through nodes, sorting into args/kwargs
    ## (we could do this more semantically, but we loop
    ## only once like this as an optimization).
    for node in nodelist:
        if isinstance(node, MacroArgNode):
            args.append(node)
        elif isinstance(node, MacroKwargNode):
            if node.keyword in macro.kwargs:
                # check that the keyword is defined as an argument for
                # the macro.
                if not node.keyword in kwargs:
                    # add the keyword argument to the dict
                    # if it's not in there
                    kwargs[node.keyword] = node
                else:
                    # raise a template syntax error if the
                    # keyword is already in the dict (thus a keyword
                    # argument was passed twice.
                    raise template.TemplateSyntaxError(
                        "{0} template tag was supplied repeated ".format(tag_name) +
                        "the same keyword argument multiple times.")
            else:
                raise template.TemplateSyntaxError(
                    "{0} template tag was supplied with a ".format(tag_name) +
                    "keyword argument not defined by the {0} macro.".format(macro_name))
        else:
            raise template.TemplateSyntaxError(
                "{0} template tag received an argument that ".format(tag_name)
                "is neither a arg or a kwarg tag. Make sure there's "
                "text or template tags directly descending from the {0} tag.".format(tag_name))

    # check that there aren't more arg tags than args
    # in the macro.
    if len(args) > len(macro.args):
        raise template.TemplateSyntaxError(
            "{0} template tag was supplied too many ".format(tag_name) +
            "argument block tags.")
        
    macro.parser = parser
    return MacroBlockNode(macro, nodelist, args, kwargs)


class MacroArgNode(template.Node):
    """ Template node object for defining a
    positional argument to a MacroBlockNode.
    """
    def __init__(self, nodelist):
        # save the tag's contents
        self.nodelist = nodelist
    def render(self, context):
        # macro_arg tags output nothing.
        return ''



@register.tag(name="macro_arg")
def do_macro_arg(parser, token):
    """ Function taking a parsed template tag
    to a MacroArgNode.
    """
    # macro_arg takes no arguments, so we don't
    # need to split the token/do validation.
    nodelist = parser.parse(('endmacro_arg',))
    parser.delete_first_token()
    # simply save the contents to a MacroArgNode.
    return MacroArgNode(nodelist)


class MacroKwargNode(template.Node):
    """ Template node object for defining a
    keyword argument to a MacroBlockNode.
    """
    def __init__(self, keyword, nodelist):
        # save keyword so we know where to
        # substitute it later.
        self.keyword = keyword
        # save the tag's contents
        self.nodelist = nodelist

    def render(self, context):
        # macro_kwarg tags output nothing.
        return ''


@register.tag(name="macro_kwarg")
def do_macro_kwarg(parser, token):
    """ Function taking a parsed template tag
    to a MacroKwargNode.
    """
    try:
        tag_name, keyword = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "{0} tag requires exactly one argument, a keyword".format(
            token.contents.split()[0]))
    
    # add some validation of the keyword argument here.
    nodelist = parser.parse(('endmacro_kwarg', ))
    parser.delete_first_token()
    return MacroKwargNode(keyword, nodelist)
