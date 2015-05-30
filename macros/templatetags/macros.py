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
from django.template.loader import get_template

register = template.Library()


def _setup_macros_dict(parser):
    """ initiates the _macros attribute on the parser
    object, allowing for storage of the macros in the parser.
    """
    # Each macro is stored in a new attribute
    # of the 'parser' class. That way we can access it later
    # in the template when processing 'use_macro' tags.
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
        # convert template variable defaults into resolved
        # variables.
        #
        # recall all defaults are template variables
        self.kwargs = {k: v.resolve(context)
                       for k, v in self.kwargs.items()}

        # empty string - {% macro %} tag has no output
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
    #  r'^[A-Za-z_][\w_]*$'

    # args must be proper python variable names
    # we'll want to capture it from the regex also.
    arg_regex = r'^([A-Za-z_][\w_]*)$'

    # kwargs must be proper variable names with a
    # default value, name="value", or name=value if
    # value is a template variable (potentially with
    # filters).
    # we'll want to capture the name and value from
    # the regex as well.
    kwarg_regex = (
        r'^([A-Za-z_][\w_]*)=(".*"|{0}.*{0}|[A-Za-z_][\w_]*)$'.format("'"))
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
    nodelist = parser.parse(('endmacro',))
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

    def __init__(self, macros):
        self.macros = macros

    def render(self, context):
        # render all macro definitions in the current
        # context to set their template variable default
        # arguments:
        for macro in self.macros:
            macro.render(context)

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
            "'{0}' tag requires exactly one argument (filename)".format(
                token.contents.split()[0]))
    if filename[0] in ('"', "'") and filename[-1] == filename[0]:
        filename = filename[1:-1]
    else:
        raise template.TemplateSyntaxError(
            "Malformed argument to the {0} template tag."
            " Argument must be in quotes.".format(tag_name)
        )
    t = get_template(filename)
    macros = t.nodelist.get_nodes_by_type(DefineMacroNode)
    # make sure the _macros attribute dictionary is instantiated
    # on the parser, then add the macros to it.
    _setup_macros_dict(parser)
    for macro in macros:
        parser._macros[macro.name] = macro
    # pass macros to LoadMacrosNode so that it can
    # resolve the macros template variable kwargs on render
    return LoadMacrosNode(macros)


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
        for name, default in self.macro.kwargs.items():
            if name in self.kwargs:
                context[name] = self.kwargs[name].resolve(context)
            else:
                if isinstance(default, template.Variable):
                    # variables must be resolved explicitly,
                    # because otherwise if macro's loaded from
                    # a separate file things will break
                    context[name] = default.resolve(context)
                else:
                    context[name] = default

        # return the nodelist rendered in the adjusted context
        return self.macro.nodelist.render(context)


def parse_macro_params(token):
    """
    Common parsing logic for both use_macro and macro_block
    """
    try:
        bits = token.split_contents()
        tag_name, macro_name, values = bits[0], bits[1], bits[2:]
    except IndexError:
        raise template.TemplateSyntaxError(
            "{0} tag requires at least one argument (macro name)".format(
                token.contents.split()[0]))

    args = []
    kwargs = {}

    # leaving most validation up to the template.Variable
    # class, but use regex here so that validation could
    # be added in future if necessary.
    kwarg_regex = (
        r'^([A-Za-z_][\w_]*)=(".*"|{0}.*{0}|[A-Za-z_][\w_]*)$'.format(
            "'"))
    arg_regex = r'^([A-Za-z_][\w_]*|".*"|{0}.*{0}|(\d+))$'.format(
        "'")
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

    return tag_name, macro_name, args, kwargs


@register.tag(name="use_macro")
def do_usemacro(parser, token):
    """ The function taking a parsed template tag
    and returning a UseMacroNode.
    """
    tag_name, macro_name, args, kwargs = parse_macro_params(token)
    try:
        macro = parser._macros[macro_name]
    except (AttributeError, KeyError):
        raise template.TemplateSyntaxError(
            "Macro '{0}' is not defined previously to the {1} tag".format(
                macro_name, tag_name))
    macro.parser = parser
    return UseMacroNode(macro, args, kwargs)


class MacroBlockNode(UseMacroNode):
    """ Template node object for the extended
    syntax macro useage.
    """

    def __init__(self, macro, nodelist, args, kwargs):
        self.nodelist = nodelist
        super(MacroBlockNode, self).__init__(macro, args, kwargs)


@register.tag(name="macro_block")
def do_macro_block(parser, token):
    """ Function taking parsed template tag
    to a MacroBlockNode.
    """
    tag_name, macro_name, args, kwargs = parse_macro_params(token)
    # could add extra validation on the macro_name tag
    # here, but probably don't need to since we're checking
    # if there's a macro by that name anyway.
    try:
        # see if the macro is in the context.
        macro = parser._macros[macro_name]
    except (AttributeError, KeyError):
        raise template.TemplateSyntaxError(
            "Macro '{0}' is not defined ".format(macro_name) +
            "previously to the {0} tag".format(tag_name))
    # get the arg and kwarg nodes from the nodelist
    nodelist = parser.parse(('endmacro_block',))
    parser.delete_first_token()

    # Loop through nodes, sorting into args/kwargs
    # (we could do this more semantically, but we loop
    # only once like this as an optimization).
    for node in nodelist:
        if isinstance(node, MacroKwargNode):
            if node.keyword in macro.kwargs:
                # check that the keyword is defined as an argument for
                # the macro.
                if node.keyword not in kwargs:
                    # add the keyword argument to the dict
                    # if it's not in there
                    kwargs[node.keyword] = node
                else:
                    # raise a template syntax error if the
                    # keyword is already in the dict (thus a keyword
                    # argument was passed twice.
                    raise template.TemplateSyntaxError(
                        "{0} template tag was supplied "
                        "the same keyword argument multiple times.".format(
                            tag_name))
            else:
                raise template.TemplateSyntaxError(
                    "{0} template tag was supplied with a "
                    "keyword argument not defined by the {1} macro.".format(
                        tag_name, macro_name))
        elif isinstance(node, MacroArgNode):
            # note that MacroKwargNode is also a MacroArgNode,
            # so this must be under else/elif statement
            args.append(node)
        elif not isinstance(node, template.TextNode) or node.s.strip() != "":
            # whitespace is allowed, anything else is not
            raise template.TemplateSyntaxError(
                "{0} template tag received an argument that "
                "is neither a arg or a kwarg tag. Make sure there's "
                "text or template tags directly descending "
                "from the {0} tag.".format(tag_name))

    # check that there aren't more arg tags than args
    # in the macro.
    if len(args) > len(macro.args):
        raise template.TemplateSyntaxError(
            "{0} template tag was supplied too many arg block tags.".format(
                tag_name))

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

    def resolve(self, context):
        # we have a "resolve" method similar with Variable,
        # so rendering code won't have to make any distinctions
        return self.nodelist.render(context)


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


class MacroKwargNode(MacroArgNode):
    """ Template node object for defining a
    keyword argument to a MacroBlockNode.
    """

    def __init__(self, keyword, nodelist):
        # save keyword so we know where to substitute it later.
        self.keyword = keyword
        super(MacroKwargNode, self).__init__(nodelist)

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
    nodelist = parser.parse(('endmacro_kwarg',))
    parser.delete_first_token()
    return MacroKwargNode(keyword, nodelist)
