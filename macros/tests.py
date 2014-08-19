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
    # test using a filter with the use_macro syntax
    USE_MACRO1_WITH_FILTER = (
        "{% use_macro macro1 'foobar'|join:'-' %}")
    MACRO1_WITH_FILTER_RENDERED = (
        "first arg: f-o-o-b-a-r; second arg: ; "
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

    def test_use_macro_with_filter(self):
        """ make sure that filters work on args and kwargs
        when using the use_macro syntax.
        """
        t = Template(self.LOAD_MACROS + self.MACRO1_DEFINITION +
            self.USE_MACRO1_WITH_FILTER)
        c = Context({})
        self.assertEqual(t.render(c), self.MACRO1_WITH_FILTER_RENDERED)

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

    # test exceptions
