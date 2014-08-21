from django.test import TestCase
from django import template
from django.template import Template, Context
from django.shortcuts import render_to_response

# Parser creation factory for testing
import django.template.base as template_base

def make_parser(template_string):
    return template_base.Parser(
        template_base.Lexer(
            template_string,
            template_base.StringOrigin(template_string)).tokenize())


# Tests for repeatedblocks.py
from .templatetags.repeatedblocks import set_repeated_blocks, BlockNode

class RepeatedBlocksTagsTests(TestCase):

    # generate test templates from these base
    # strings to be more dry/in case tag syntax
    # changes later.
    LOAD_STRING = "{% load repeatedblocks %}"
    # define first repeated_block strings
    RBLOCK_1_NAME = "rblock1"
    DEFINE_RBLOCK_1 = (
            "{{% repeated_block {0} %}}".format(RBLOCK_1_NAME) + 
                "string1"
            "{% endblock %}")
    REPEAT_RBLOCK_1 = "{{% repeat {0} %}}".format(RBLOCK_1_NAME)
    # define second repeated_block strings
    RBLOCK_2_NAME = "rblock2"
    DEFINE_RBLOCK_2 = (
            "{{% repeated_block {0} %}}".format(RBLOCK_2_NAME) + 
                "string2"
            "{% endblock %}")
    REPEAT_RBLOCK_2 = "{{% repeat {0} %}}".format(RBLOCK_2_NAME)
    # too few and too many args
    TOO_FEW_REPEATED_BLOCK = "{% repeated_block %}"
    TOO_MANY_REPEATED_BLOCK = "{% repeated_block arg1 arg2 %}"
    TOO_FEW_REPEAT = "{% repeat %}"
    TOO_MANY_REPEAT = "{% repeat arg1 arg2 %}"
    
    # test assumptions
    def test_creates_normal_block(self):
        """ It is assumed that the block node created
        by the repeated block tag, and the block node
        created by the usual block tag are identical.
        """
        t = Template(
            self.LOAD_STRING + self.DEFINE_RBLOCK_1)
        # assert that there is only two nodes in template
            # first node is the load tag
            # second node is the block node
        self.assertEqual(len(t.nodelist), 2)
        # make sure that the second node is a block node
        self.assertIsInstance(t.nodelist[1], BlockNode)
        # make sure that node is the block node we expect it to be
        self.assertEqual(t.nodelist[1].name, self.RBLOCK_1_NAME)

    # test functionality

    ## test set_repeated_blocks
    def test_set_repeated_blocks_sets_variable(self):
        """ Set repeated blocks must set the _repeated_blocks
        variable on the parser.
        """
        p = make_parser("A short template")
        # check that the parser doesn't initially have the
        # _repeated_blocks attribute
        self.assertFalse(hasattr(p, "_repeated_blocks"))
        # check that set_repeated_blocks actually sets the
        # attribute.
        set_repeated_blocks(p)
        self.assertTrue(hasattr(p, "_repeated_blocks"))

    def test_set_repeated_blocks_doesnt_overwrite(self):
        """ Set repeated blocks must not overwrite the
        _repeated_blocks variable on the parser, if it
        already exists.
        """
        p = make_parser("A short template")
        # set the attribute to a specific dict
        dic = {'foo': 'bar', }
        p._repeated_blocks = dic
        # call set_repeated_blocks and test that
        # the dict hasn't been overwritten.
        set_repeated_blocks(p)
        self.assertEqual(p._repeated_blocks, dic)

    def test_set_repeated_blocks_initialize_empty(self):
        """ Set repeated blocks must initialize the
        the _repeated_blocks variable as an empty dict.
        """
        p = make_parser("A short template")
        set_repeated_blocks(p)
        self.assertEqual(p._repeated_blocks, {})

    ## test repeated_block and repeat
    def test_repeated_block_repeats_once(self):
        """ The repeated blocks should be able to repeat
        an arbitrary number of times, this tests that it
        repeats once.
        """
        t = Template(
            self.LOAD_STRING + self.DEFINE_RBLOCK_1 +
            self.REPEAT_RBLOCK_1)
        c = Context({})
        self.assertEqual(t.render(c), "string1string1")
        

    def test_repeated_block_repeats_twice(self):
        """ The repeated blocks should be able to repeat
        an arbitrary number of times, this tests that it
        repeats twice.
        """
        t = Template(
            self.LOAD_STRING + self.DEFINE_RBLOCK_1 +
            self.REPEAT_RBLOCK_1 +
            self.REPEAT_RBLOCK_1)
        c = Context({})
        self.assertEqual(t.render(c), "string1string1string1")

    def test_repeated_block_repeats_thrice(self):
        """ The repeated blocks should be able to repeat
        an arbitrary number of times, this tests that it
        repeats thrice.
        """
        t = Template(
            self.LOAD_STRING + self.DEFINE_RBLOCK_1 +
            self.REPEAT_RBLOCK_1 +
            self.REPEAT_RBLOCK_1 +
            self.REPEAT_RBLOCK_1)
        c = Context({})
        self.assertEqual(t.render(c),
                         "string1string1string1string1")

    def test_two_distinct_repeat_blocks(self):
        """ Multiple repeated blocks should be able to
        exist and work at the same time.
        """
        t = Template(
            self.LOAD_STRING + self.DEFINE_RBLOCK_1 +
            self.REPEAT_RBLOCK_1 +
            self.DEFINE_RBLOCK_2 +
            self.REPEAT_RBLOCK_1 +
            self.REPEAT_RBLOCK_2 +
            self.REPEAT_RBLOCK_1)
        c = Context({})
        self.assertEqual(t.render(c),
                         "string1string1string2string1string2string1")

    # test exceptions
    def test_repeat_coming_before_repeated_block(self):
        """ If the repeat tag comes before the repeated
        block tag, it should throw an exception.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^No repeated block .+ tag was found before the .+ tag$",
            Template,
            # call Template on the following string/template
            self.LOAD_STRING + self.REPEAT_RBLOCK_1 +
            self.DEFINE_RBLOCK_1,)
    
    def test_repeat_having_no_block(self):
        """ If repeat is called without a repeated block
        definition existing, than repeat should throw an
        exception.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^No repeated block .+ tag was found before the .+ tag$",
            Template,
            # call Template on the following string/template
            self.LOAD_STRING + self.REPEAT_RBLOCK_2)

    def test_repeat_having_no_block_of_same_name(self):
        """ If repeat is called without a repeated block of
        the corresponding name existing, than repeat should
        throw an exception.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^No repeated block {0} tag was found before the .+ tag$".format(
                self.RBLOCK_2_NAME),
            Template,
            # call Template on the following string/template
            self.LOAD_STRING + self.DEFINE_RBLOCK_1 +
            self.REPEAT_RBLOCK_2)

    def test_repeated_block_with_no_args(self):
        """ repeated_block should throw an exception when
        called without arguments.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ tag takes only one argument$",
            Template,
            self.LOAD_STRING + self.TOO_FEW_REPEATED_BLOCK)
    
    def test_repeated_block_with_too_many_args(self):
        """ repeated_block should throw an exception when
        called with too many arguments.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ tag takes only one argument$",
            Template,
            self.LOAD_STRING + self.TOO_MANY_REPEATED_BLOCK)

    def test_repeat_with_no_args(self):
        """ repeat should throw an exception when
        called without arguments.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ tag takes only one argument$",
            Template,
            self.LOAD_STRING + self.TOO_FEW_REPEAT)
    
    def test_repeat_with_too_many_args(self):
        """ repeat should throw an exception when
        called with too many arguments.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ tag takes only one argument$",
            Template,
            self.LOAD_STRING + self.TOO_MANY_REPEAT)


# Tests for macros.py
from .templatetags.macros import _setup_macros_dict

class MacrosTests(TestCase):

    # Template pieces
        # (all templates are at the top so they can
        # be easily changed/reused 
    LOAD_MACROS = "{% load macros %}"
    # load macros test
    TEST_LOADMACROS_TAG = (
        "{% loadmacros 'macros/tests/testmacros.html' %}"
        "{% use_macro test_macro 'foo' 'bar' %}")
    # define a macro
    MACRO1_DEFINITION = (
        "{% macro macro1 first_arg second_arg first_kwarg=''"
        " second_kwarg='default' %}"
            "first arg: {{ first_arg }}; "
            "second arg: {{ second_arg }}; "
            "first_kwarg: {{ first_kwarg }}; "
            "second_kwarg: {{ second_kwarg }};"
        "{% endmacro %}")
    # test default values
    USE_MACRO1_WITH_DEFAULTS = (
        "{% use_macro macro1 'foo' 'bar' %}")
    MACRO1_BLOCK_WITH_DEFAULTS = (
        "{% macro_block macro1 %}"
            "{% macro_arg %}foo{% endmacro_arg %}"
            "{% macro_arg %}bar{% endmacro_arg %}"
        "{% endmacro_block %}")
    MACRO1_WITH_DEFAULTS_RENDERED = (
        "first arg: foo; second arg: bar; "
        "first_kwarg: ; second_kwarg: default;")
    # test using only one default, overriding the other
    USE_MACRO1_WITH_ONE_DEFAULT = (
        "{% use_macro macro1 'bar' 'foo' first_kwarg='value' %}")
    MACRO1_BLOCK_WITH_ONE_DEFAULT = (
        "{% macro_block macro1 %}"
            "{% macro_arg %}bar{% endmacro_arg %}"
            "{% macro_arg %}foo{% endmacro_arg %}"
            "{% macro_kwarg first_kwarg %}value{% endmacro_kwarg %}"
        "{% endmacro_block %}")
    MACRO1_WITH_ONE_DEFAULT_RENDERED = (
        "first arg: bar; second arg: foo; "
        "first_kwarg: value; second_kwarg: default;")
    # test overriding all defaults
    USE_MACRO1_WITH_NO_DEFAULTS = (
        "{% use_macro macro1 'one' 'two' "
        "first_kwarg='value1' second_kwarg='value2' %}")
    MACRO1_BLOCK_WITH_NO_DEFAULTS = (
        "{% macro_block macro1 %}"
            "{% macro_arg %}one{% endmacro_arg %}"
            "{% macro_arg %}two{% endmacro_arg %}"
            "{% macro_kwarg first_kwarg %}value1{% endmacro_kwarg %}"
            "{% macro_kwarg second_kwarg %}value2{% endmacro_kwarg %}"
        "{% endmacro_block %}")
    MACRO1_WITH_NO_DEFAULTS_RENDERED = (
        "first arg: one; second arg: two; "
        "first_kwarg: value1; second_kwarg: value2;")
    # test using macro with no args
    USE_MACRO1_WITH_NO_ARGS = (
        "{% use_macro macro1 %}")
    MACRO1_BLOCK_WITH_NO_ARGS = (
        "{% macro_block macro1 %}{% endmacro_block %}")
    MACRO1_WITH_NO_ARGS_RENDERED = (
        "first arg: ; second arg: ; "
        "first_kwarg: ; second_kwarg: default;")
    # Define a second macro (test lexical scoping of args)
    MACRO2_DEFINITION = (
        "{% macro macro2 first_arg second_arg "
        "first_kwarg='one' second_kwarg='two' %}"
            "second macro contents:{{ first_arg }},"
            "{{ second_arg }},{{ first_kwarg }},"
            "{{ second_kwarg }};"
        "{% endmacro %}")
    USE_MACRO2 = (
        "{% use_macro macro2 'first' 'second' "
        "first_kwarg='new_one' %}")
    MACRO2_BLOCK = (
        "{% macro_block macro2 %}"
            "{% macro_arg %}first{% endmacro_arg %}"
            "{% macro_arg %}second{% endmacro_arg %}"
            "{% macro_kwarg first_kwarg %}new_one{% endmacro_kwarg %}"
        "{% endmacro_block %}")
    MACRO2_RENDERED = (
        "second macro contents:first,second,new_one,two;")
    # test argument parsing with equals signs in them
    USE_MACRO2_WITH_ARG_EQUALS_SIGN = (
        "{% use_macro macro2 'a=b' %}")
    MACRO2_WITH_ARG_EQUALS_SIGN_RENDERED = (
        "second macro contents:a=b,,one,two;")
    USE_MACRO2_WITH_KWARG_EQUALS_SIGN = (
        '{% use_macro macro2 first_kwarg="a=b" %}')
    MACRO2_WITH_KWARG_EQUALS_SIGN_RENDERED = (
        'second macro contents:,,a=b,two;')
    # test defining a macro with an equals sign in a default argument.
    MACRO3_DEFINITION = (
        "{% macro macro3 arg kwarg='a=b' %}"
            "{{ arg }}{{ kwarg }};"
        "{% endmacro %}")
    USE_MACRO3 = (
        "{% use_macro macro3 %}")
    MACRO3_RENDERED = "a=b;"
    # test using context variable with macros
    USE_MACRO3_WITH_VARIABLE_ARG = (
        "{% use_macro macro3 foo kwarg='' %}")
    USE_MACRO3_WITH_VARIABLE_KWARG = (
        "{% use_macro macro3 kwarg=foo %}")
    MACRO3_BLOCK_WITH_VARIABLE_INSIDE = (
        "{% macro_block macro3 %}"
            "{% macro_kwarg kwarg %}"
                "{{ foo }}"
            "{% endmacro_kwarg %}"
        "{% endmacro_block %}")
    MACRO3_WITH_VARIABLE_RENDERED = "bar;"
    FOO_VALUE = "bar"
    # test using a context variable to define a macro default
    MACRO4_DEFINITION = (
        "{% macro macro4 kwarg=foo %}"
            "{{ kwarg }};"
        "{% endmacro %}")
    USE_MACRO4_WITH_VALUE = (
        "{% use_macro macro4 kwarg='value' %}")
    USE_MACRO4_WITHOUT_VALUE = (
        "{% use_macro macro4 %}")
    MACRO4_WITH_VALUE_RENDERED = (
        "value;")
    MACRO4_WITHOUT_VALUE_RENDERED = (
        "bar;")
    # test defining a macro with no args or kwargs
    MACRO5_DEFINITION = (
        "{% macro macro5 %}"
            "contents"
        "{% endmacro %}")
    USE_MACRO5 = "{% use_macro macro5 %}"
    MACRO5_RENDERED = "contents"
    # exceptions testing templates are kept in the definition
    # of the exceptions tests.
    
    # test functionality

    ## test _setup_macros_dict
    def test_set__setup_macros_dict_sets_variable(self):
        """ _setup_macros_dict must set the _macros
        variable on the parser.
        """
        p = make_parser("A short template")
        # check that the parser doesn't initially have the
        # _macros attribute
        self.assertFalse(hasattr(p, "_macros"))
        # check that _setup_macros_dict actually sets the
        # attribute.
        _setup_macros_dict(p)
        self.assertTrue(hasattr(p, "_macros"))

    def test_set__setup_macros_dict_doesnt_overwrite(self):
        """ _setup_macros_dict must not overwrite the
        _macros variable on the parser, if it already
        exists.
        """
        p = make_parser("A short template")
        # set the attribute to a specific dict
        dic = {'foo': 'bar', }
        p._macros = dic
        # call _setup_macros_dict and test that
        # the dict hasn't been overwritten.
        _setup_macros_dict(p)
        self.assertEqual(p._macros, dic)

    def test_set__setup_macros_dict_initialize_empty(self):
        """ Set repeated blocks must initialize the
        the _repeated_blocks variable as an empty dict.
        """
        p = make_parser("A short template")
        _setup_macros_dict(p)
        self.assertEqual(p._macros, {})

    ## test load macros

    #### contents of testmacros.html:
    """
    {% load macros %}

    {% macro test_macro arg1 arg2 kwarg1="default" %}
            arg1: {{ arg1 }};
            arg2: {{ arg2 }};
            kwarg1: {{ kwarg1 }};
    {% endmacro %}
    """

    def test_load_macros_works(self):
        """ Load macros should make the test macro
        available to the template.
        """
        p = make_parser(self.LOAD_MACROS + self.TEST_LOADMACROS_TAG)
        # parse the template to run the template tags
        nodelist = p.parse()
        # check that the macro is added to the parser
        self.assertTrue(hasattr(p, "_macros"))
        self.assertIn("test_macro", p._macros)
        # render nodelist
        c = Context({})
        rendered_template = nodelist.render(c)
        # check that the macro renders in the new template
        self.assertEqual(rendered_template,
            "arg1: foo;arg2: bar;kwarg1: default;")
    
    ## test macro, use_macro, and macro_block
    def test_macro_sets_in_parser(self):
        """ check that the macro tag actually sets
        the node in the parser.
        """
        p = make_parser(self.LOAD_MACROS + self.MACRO1_DEFINITION)
        # parse the template to run the template tags
        nodelist = p.parse()
        # check that the macro is added to the parser
        self.assertTrue(hasattr(p, "_macros"))
        self.assertIn("macro1", p._macros)

    def test_use_macro_with_defaults(self):
        """ make sure that the use_macro tag uses default
        values for kwargs when values aren't supplied
        """
        t = Template(self.LOAD_MACROS + self.MACRO1_DEFINITION +
            self.USE_MACRO1_WITH_DEFAULTS)
        c = Context({})
        self.assertEqual(t.render(c), self.MACRO1_WITH_DEFAULTS_RENDERED)

    def test_macro_block_with_defaults(self):
        """ make sure that the macro_block tag uses default
        values for kwargs when values aren't supplied
        """
        t = Template(self.LOAD_MACROS + self.MACRO1_DEFINITION +
            self.MACRO1_BLOCK_WITH_DEFAULTS)
        c = Context({})
        self.assertEqual(t.render(c), self.MACRO1_WITH_DEFAULTS_RENDERED)

    def test_use_macro_with_one_default(self):
        """ make sure that the use_macro tag uses one default
        value for a kwarg when value isn't supplied.
        """
        t = Template(self.LOAD_MACROS + self.MACRO1_DEFINITION +
            self.USE_MACRO1_WITH_ONE_DEFAULT)
        c = Context({})
        self.assertEqual(t.render(c), self.MACRO1_WITH_ONE_DEFAULT_RENDERED)

    def test_macro_block_with_one_default(self):
        """ make sure that the macro_block tag uses one default
        value for a kwarg when value isn't supplied.
        """
        t = Template(self.LOAD_MACROS + self.MACRO1_DEFINITION +
            self.MACRO1_BLOCK_WITH_ONE_DEFAULT)
        c = Context({})
        self.assertEqual(t.render(c), self.MACRO1_WITH_ONE_DEFAULT_RENDERED)

    def test_use_macro_with_no_defaults(self):
        """ make sure that the use_macro tag uses no default
        values for a kwarg when both values are supplied.
        """
        t = Template(self.LOAD_MACROS + self.MACRO1_DEFINITION +
            self.USE_MACRO1_WITH_NO_DEFAULTS)
        c = Context({})
        self.assertEqual(t.render(c), self.MACRO1_WITH_NO_DEFAULTS_RENDERED)

    def test_macro_block_with_no_defaults(self):
        """ make sure that the macro_block tag uses no default
        values for kwargs when both values are supplied.
        """
        t = Template(self.LOAD_MACROS + self.MACRO1_DEFINITION +
            self.MACRO1_BLOCK_WITH_NO_DEFAULTS)
        c = Context({})
        self.assertEqual(t.render(c), self.MACRO1_WITH_NO_DEFAULTS_RENDERED)

    def test_use_macro_with_no_args(self):
        """ make sure that the use_macro tag fails variables
        silently when no args are supplied.
        """
        t = Template(self.LOAD_MACROS + self.MACRO1_DEFINITION +
            self.USE_MACRO1_WITH_NO_ARGS)
        c = Context({})
        self.assertEqual(t.render(c), self.MACRO1_WITH_NO_ARGS_RENDERED)

    def test_macro_block_with_no_args(self):
        """ make sure that the macro_block tag fails variables
        silently when no args are supplied.
        """
        t = Template(self.LOAD_MACROS + self.MACRO1_DEFINITION +
            self.MACRO1_BLOCK_WITH_NO_ARGS)
        c = Context({})
        self.assertEqual(t.render(c), self.MACRO1_WITH_NO_ARGS_RENDERED)

    def test_lexical_scoping(self):
        """ make sure that args and kwargs in macros are lexically
        to just that macro.
        """
        c = Context({})
        # first template test: use_macro with use_macro
            # test to look for conflicts between scopes,
            # defaults overriding non-defaults across scope,
            # and vice versa.
        t1 = Template(self.LOAD_MACROS + self.MACRO1_DEFINITION +
            self.MACRO2_DEFINITION + self.USE_MACRO1_WITH_ONE_DEFAULT +
            self.USE_MACRO2)
        self.assertEqual(t1.render(c),
            self.MACRO1_WITH_ONE_DEFAULT_RENDERED + self.MACRO2_RENDERED)
        # second template test
            # test use_macro with macro_block
        t2 = Template(self.LOAD_MACROS + self.MACRO1_DEFINITION +
            self.MACRO2_DEFINITION + self.USE_MACRO1_WITH_ONE_DEFAULT +
            self.MACRO2_BLOCK)
        self.assertEqual(t2.render(c),
            self.MACRO1_WITH_ONE_DEFAULT_RENDERED + self.MACRO2_RENDERED)
        # third template test
            # test macro_block with use_macro
        t3 = Template(self.LOAD_MACROS + self.MACRO1_DEFINITION +
            self.MACRO2_DEFINITION + self.MACRO1_BLOCK_WITH_ONE_DEFAULT +
            self.USE_MACRO2)
        self.assertEqual(t3.render(c),
            self.MACRO1_WITH_ONE_DEFAULT_RENDERED + self.MACRO2_RENDERED)
        # fourth template test
            # test macro_block with macro_block
        t4 = Template(self.LOAD_MACROS + self.MACRO1_DEFINITION +
            self.MACRO2_DEFINITION + self.MACRO1_BLOCK_WITH_ONE_DEFAULT +
            self.MACRO2_BLOCK)
        self.assertEqual(t4.render(c),
            self.MACRO1_WITH_ONE_DEFAULT_RENDERED + self.MACRO2_RENDERED)
        # test a different combination of macro useage
        t5 = Template(self.LOAD_MACROS + self.MACRO2_DEFINITION +
            self.MACRO1_DEFINITION + self.USE_MACRO1_WITH_NO_ARGS +
            self.USE_MACRO2)
        self.assertEqual(t5.render(c),
            self.MACRO1_WITH_NO_ARGS_RENDERED + self.MACRO2_RENDERED)

    def test_use_macro_with_macro_block(self):
        """ test that use_macro and macro_block may
        be used in the same template.
        """
        t = Template(self.LOAD_MACROS + self.MACRO1_DEFINITION +
            self.USE_MACRO1_WITH_DEFAULTS + ";" +
            self.MACRO1_BLOCK_WITH_DEFAULTS)
        c = Context({})
        self.assertEqual(t.render(c), self.MACRO1_WITH_DEFAULTS_RENDERED +
            ";" + self.MACRO1_WITH_DEFAULTS_RENDERED)

    def test_define_macro_with_equals_sign(self):
        """ test that when a kwarg's default value has an equals
        sign, it won't throw a bug.
        """
        t = Template(self.LOAD_MACROS + self.MACRO3_DEFINITION +
            self.USE_MACRO3)
        c = Context({})
        self.assertEqual(t.render(c),
            self.MACRO3_RENDERED)

    def test_arg_with_equals_sign(self):
        """ test that when an arg has an equals sign surrounded
        by quotes, the arg still parses correctly.
        """
        t = Template(self.LOAD_MACROS + self.MACRO2_DEFINITION +
            self.USE_MACRO2_WITH_ARG_EQUALS_SIGN)
        c = Context({})
        self.assertEqual(t.render(c),
            self.MACRO2_WITH_ARG_EQUALS_SIGN_RENDERED)

    def test_kwarg_with_equals_sign(self):
        """ test that when a kwarg is set to a value with an equals
        sign in it, that the kwarg still parses correctly.
        """
        t = Template(self.LOAD_MACROS + self.MACRO2_DEFINITION +
            self.USE_MACRO2_WITH_KWARG_EQUALS_SIGN)
        c = Context({})
        self.assertEqual(t.render(c),
            self.MACRO2_WITH_KWARG_EQUALS_SIGN_RENDERED)

    def test_using_context_variable_in_use_macro_arg(self):
        """ Use macro is meant to be able to accept context variables
        in its args.
        """
        t = Template(self.LOAD_MACROS + self.MACRO3_DEFINITION +
            self.USE_MACRO3_WITH_VARIABLE_ARG)
        c = Context({'foo': self.FOO_VALUE})
        self.assertEqual(t.render(c), self.MACRO3_WITH_VARIABLE_RENDERED)

    def test_using_context_variable_in_use_macro_kwarg(self):
        """ Use macro is meant to be able to accept context variables
        in its kwargs.
        """
        t = Template(self.LOAD_MACROS + self.MACRO3_DEFINITION +
            self.USE_MACRO3_WITH_VARIABLE_KWARG)
        c = Context({'foo': self.FOO_VALUE})
        self.assertEqual(t.render(c), self.MACRO3_WITH_VARIABLE_RENDERED)
        
    def test_using_context_variable_in_macro_block(self):
        """ Macro block is meant to be able to accept context variables
        inside it's sub blocks.
        """
        t = Template(self.LOAD_MACROS + self.MACRO3_DEFINITION +
            self.MACRO3_BLOCK_WITH_VARIABLE_INSIDE)
        c = Context({'foo': self.FOO_VALUE})
        self.assertEqual(t.render(c), self.MACRO3_WITH_VARIABLE_RENDERED)

    def test_using_context_variable_in_defining_macro(self):
        """ People should be able to use context variables in defining
        default values for templates.
        """
        t = Template(self.LOAD_MACROS + self.MACRO4_DEFINITION +
            self.USE_MACRO4_WITH_VALUE + self.USE_MACRO4_WITHOUT_VALUE)
        c = Context({'foo': self.FOO_VALUE})
        self.assertEqual(t.render(c), self.MACRO4_WITH_VALUE_RENDERED +
            self.MACRO4_WITHOUT_VALUE_RENDERED)

    def test_default_template_variables_set_at_definition(self):
        """ when a macro tag uses a template variable to
        set a default value for a kwarg, the default value
        should be what the context variable was at the definition
        of the macro, and so should not change later if the variable
        does.
        """
        t = Template(self.LOAD_MACROS + self.MACRO4_DEFINITION +
            "{% with 'new value' as foo %}" +
                self.USE_MACRO4_WITHOUT_VALUE +
            "{% endwith %}")
        c = Context({'foo': self.FOO_VALUE})
        # default value should still be 'bar' or self.FOO_VALUE as
        # the variable was at the macro's definition.
        self.assertEqual(t.render(c), self.MACRO4_WITHOUT_VALUE_RENDERED)

    def test_defining_macro_with_no_args(self):
        """ Macros should be useable with no arguments, and just a macro
        name.
        """
        t = Template(self.LOAD_MACROS + self.MACRO5_DEFINITION +
            self.USE_MACRO5)
        c = Context({})
        self.assertEqual(t.render(c), self.MACRO5_RENDERED)
    
    # test exceptions

    def test_macro_with_no_end_tag(self):
        """ when the macro tag doesn't have an end tag,
        it should raise an exception.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^Unclosed tag .+\. Looking for one of: .+$",
            Template,
            self.LOAD_MACROS + "{% macro macro_name %}some text")

    def test_macro_with_no_macro_name_exception(self):
        """ A macro tag without a macro name should raise
        a too few arguments exception.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ tag requires at least one argument \(macro name\)$",
            Template,
            self.LOAD_MACROS + "{% macro %}{% endmacro %}")

    def test_macro_raises_malformed_argument_exception_for_arg(self):
        """ A macro tag should raise an exception if an arg
        is malformed.
        """
        # quotes around the arg definition
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^Malformed arguments to the .+ tag.$",
            Template,
            self.LOAD_MACROS + "{% macro macro_name 'arg' %}"
            "{% endmacro %}")

        # end quote on the arg definition
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^Malformed arguments to the .+ tag.$",
            Template,
            self.LOAD_MACROS + "{% macro macro_name arg' %}"
            "{% endmacro %}")

    def test_macro_raises_malformed_argument_exception_for_kwarg(self):
        """ A macro tag should raise an exception if a kwarg
        is malformed.
        """
        # default value not entirely in quotes
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^Malformed arguments to the .+ tag.$",
            Template,
            self.LOAD_MACROS + "{% macro macro_name kw=a'arg' %}"
            "{% endmacro %}")

        # keyword in quotes
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^Malformed arguments to the .+ tag.$",
            Template,
            self.LOAD_MACROS + "{% macro macro_name 'kw'=aarg %}"
            "{% endmacro %}")

    def test_macro_raises_variable_missing_exception(self):
        """ if a macro tag is called with a default set to
        a variable that is not in the context, it should
        raise a VariableDoesNotExist error.
        """
        # argument only throws error when the template is
        # actually rendered, because that is when variables
        # are resolved into contexts.
        t = Template(self.LOAD_MACROS +
            "{% macro some_macro kwarg=foo %}text{% endmacro %}")
        self.assertRaises(
            template.VariableDoesNotExist,
            t.render,
            Context({}))

    def test_macro_raises_malformed_argument_exception_for_filter(self):
        """ If the user attempts to use a filter on an argument,
        the macro tag should raise a malformed arguments exception.
        """
        # use filter on template variable
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^Malformed arguments to the .+ tag.$",
            Template,
            self.LOAD_MACROS + "{% macro macro_name kwarg=arg|join:\",\" %}"
            "{% endmacro %}")

        # use filter on hard-coded string
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^Malformed arguments to the .+ tag.$",
            Template,
            self.LOAD_MACROS + "{% macro macro_name kwarg='arg'|join:\",\" %}"
            "{% endmacro %}")

    def test_load_macros_raises_no_arguments_exception(self):
        """ If the loadmacros tag is called without a filename,
        it should raise a template syntax error.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ tag requires exactly one argument \(filename\)$",
            Template,
            self.LOAD_MACROS + "{% loadmacros %}")

    def test_load_macros_raises_for_too_many_arguments(self):
        """ If the loadmacros tag is called with two or more
        arguments, it should raise an error.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ tag requires exactly one argument \(filename\)$",
            Template,
            self.LOAD_MACROS +
                "{% loadmacros 'macros/tests/testmacros.html' "
                "'macros/tests/testmacros.html' %}")

    def test_load_macros_malformed_arguments_exception(self):
        """ if the loadmacros tag's filename argument is not
        wrapped in quotes, then the tag should raise a
        template syntax error.
        """
        # malformed argument: no quotes
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^Malformed argument to the .+ template tag. "
                 "Argument must be in quotes.$",
            Template,
            self.LOAD_MACROS +
                "{% loadmacros macros/tests/testmacros.html %}")
        # malformed argument: mismatched quotes ("')
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^Malformed argument to the .+ template tag. "
                 "Argument must be in quotes.$",
            Template,
            self.LOAD_MACROS +
                "{% loadmacros \"macros/tests/testmacros.html' %}")
        # malformed argument: mismatched quotes ('")
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^Malformed argument to the .+ template tag. "
                 "Argument must be in quotes.$",
            Template,
            self.LOAD_MACROS +
                "{% loadmacros 'macros/tests/testmacros.html\" %}")
        # malformed argument: only one quote
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^Malformed argument to the .+ template tag. "
                 "Argument must be in quotes.$",
            Template,
            self.LOAD_MACROS +
                "{% loadmacros 'macros/tests/testmacros.html %}")
        
    def test_use_macro_with_no_macro_name(self):
        """ if use_macro is called without any arguments, it
        raises an exception.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ tag requires at least one argument \(macro name\)$",
            Template,
            self.LOAD_MACROS + "{% use_macro %}")

    def test_use_macro_without_macro_definition(self):
        """ if use_macro is called without a macro definition
        or with the macro definition after use_macro, then it
        should raise an exception.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^Macro .+ is not defined previously to the .+ tag$",
            Template,
            self.LOAD_MACROS + "{% use_macro macro_name %}")

    def test_use_macro_before_macro_definition(self):
        """ if use_macro comes before the definition of the macro
        it uses, then it should throw an exception.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^Macro .+ is not defined previously to the .+ tag$",
            Template,
            self.LOAD_MACROS + self.USE_MACRO2 +
                self.MACRO2_DEFINITION)

    def test_use_macro_with_malformed_arguments(self):
        """ if use_macro is passed malformed arguments, it should
        raise an exception.
        """
        # malformed arg
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^Malformed arguments to the .+ tag.$",
            Template,
            self.LOAD_MACROS + self.MACRO3_DEFINITION +
                "{% use_macro macro3 'foo'o %}")
        
        # malformed kwarg
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^Malformed arguments to the .+ tag.$",
            Template,
            self.LOAD_MACROS + self.MACRO3_DEFINITION +
                "{% use_macro macro3 kwar'g'='a=b' %}")

    def test_macro_block_with_no_macro_name(self):
        """ if macro_block is called without a macro_name, it should
        raise an exception.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r".+ tag requires exactly one argument, a macro's name",
            Template,
            self.LOAD_MACROS + self.MACRO3_DEFINITION +
                "{% macro_block %}{% endmacro_block %}")

    def test_macro_block_before_macro_definition(self):
        """ if macro_block is called before a macro's definition,
        it should raise an exception.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^Macro .+ is not defined previously to the .+ tag$",
            Template,
            self.LOAD_MACROS + "{% macro_block macro3 %}{% endmacro_block %}"
            + self.MACRO3_DEFINITION)

    def test_macro_block_with_no_macro_definition(self):
        """ if macro_block is called on a macro that hasn't
        been defined, then it should raise an exception.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^Macro .+ is not defined previously to the .+ tag$",
            Template,
            self.LOAD_MACROS + "{% macro_block macro3 %}{% endmacro_block %}")

    def test_macro_block_with_repeated_keyword(self):
        """ if the macro_block is passed the same keyword
        argument twice, it should raise an exception.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ template tag was supplied "
            r"the same keyword argument multiple times.$",
            Template,
            self.LOAD_MACROS + self.MACRO3_DEFINITION +
            "{% macro_block macro3 %}"
                "{% macro_kwarg kwarg %}"
                    "contents"
                "{% endmacro_kwarg %}"
                "{% macro_kwarg kwarg %}"
                    "values"
                "{% endmacro_kwarg %}"
            "{% endmacro_block %}")

    def test_macro_block_with_undefined_keyword(self):
        """ if macro_block is called with a keyword
        argument not defined in its macro, it should raise
        an exception.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ template tag was supplied with a "
            r"keyword argument not defined by the .+ macro.$",
            Template,
            self.LOAD_MACROS + self.MACRO3_DEFINITION +
            "{% macro_block macro3 %}"
                "{% macro_kwarg foo %}"
                    "contents"
                "{% endmacro_kwarg %}"
            "{% endmacro_block %}")
## removed these tests because I've removed the validation that prevents white
## space/text/template tags in the macro blocks.
##
##    def test_macro_block_with_text(self):
##        """ if macro_block is called with text inside it
##        not wrapped in an arg or kwarg tag, it should raise
##        an exception.
##        """
##        self.assertRaisesRegexp(
##            template.TemplateSyntaxError,
##            r"^.+ template tag received an argument that "
##            r"is neither a arg or a kwarg tag. Make sure there's "
##            r"text or template tags directly descending from the .+ tag.$",
##            Template,
##            self.LOAD_MACROS + self.MACRO3_DEFINITION +
##            "{% macro_block macro3 %}"
##                "some text outside a tag"
##                "{% macro_kwarg kwarg %}"
##                    "contents"
##                "{% endmacro_kwarg %}"
##            "{% endmacro_block %}")
##
##    def test_macro_block_with_bad_node(self):
##        """ if macro_block is called with a template tag as
##        a direct descendent of it that is not an arg or
##        kwarg tag, it should raise an exception.
##        """
##        self.assertRaisesRegexp(
##            template.TemplateSyntaxError,
##            r"^.+ template tag received an argument that "
##            r"is neither a arg or a kwarg tag. Make sure there's "
##            r"text or template tags directly descending from the .+ tag.$",
##            Template,
##            self.LOAD_MACROS + self.MACRO3_DEFINITION +
##            "{% macro_block macro3 %}"
##                "{% if True %}{% endif %}"
##                "{% macro_kwarg kwarg %}"
##                    "contents"
##                "{% endmacro_kwarg %}"
##            "{% endmacro_block %}")

    def test_macro_block_with_too_many_args(self):
        """ if macro_block is called with more args than
        defined in its macro, it should raise an exception.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ template tag was supplied too many "
            r"arg block tags.$",
            Template,
            self.LOAD_MACROS + self.MACRO3_DEFINITION +
            "{% macro_block macro3 %}"
                "{% macro_arg %}"
                    "contents one"
                "{% endmacro_arg %}"
                "{% macro_arg %}"
                    "contents two"
                "{% endmacro_arg %}"
            "{% endmacro_block %}")

    def test_macro_kwarg_with_too_few_arguments(self):
        """ if macro_kwarg tag is called with too few arguments,
        it should raise an exception.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ tag requires exactly one argument, a keyword$",
            Template,
            self.LOAD_MACROS + self.MACRO3_DEFINITION +
            "{% macro_block macro3 %}"
                "{% macro_kwarg %}"
                    "contents"
                "{% endmacro_kwarg %}"
            "{% endmacro_block %}")

    def test_macro_kwarg_with_too_many_arguments(self):
        """ if macro_kwarg tag is called with too many arguments,
        it should raise an exception.
        """
        self.assertRaisesRegexp(
            template.TemplateSyntaxError,
            r"^.+ tag requires exactly one argument, a keyword$",
            Template,
            self.LOAD_MACROS + self.MACRO3_DEFINITION +
            "{% macro_block macro3 %}"
                "{% macro_kwarg kwarg kwarg %}"
                    "contents"
                "{% endmacro_kwarg %}"
            "{% endmacro_block %}")
