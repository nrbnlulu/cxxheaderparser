# Note: testcases generated via `python -m cxxheaderparser.gentest`
from cxxheaderparser.simple import ClassScope
from cxxheaderparser.simple import NamespaceScope
from cxxheaderparser.simple import parse_string
from cxxheaderparser.simple import ParsedData
from cxxheaderparser.types import AnonymousName
from cxxheaderparser.types import ClassDecl
from cxxheaderparser.types import Field
from cxxheaderparser.types import FundamentalSpecifier
from cxxheaderparser.types import NameSpecifier
from cxxheaderparser.types import PQName
from cxxheaderparser.types import Type


def test_union_basic() -> None:
    content = """

      struct HAL_Value {
        union {
          int v_int;
          HAL_Bool v_boolean;
        } data;
      };
    """
    data = parse_string(content, cleandoc=True)

    assert data == ParsedData(
        namespace=NamespaceScope(
            classes=[
                ClassScope(
                    class_decl=ClassDecl(
                        typename=PQName(
                            segments=[NameSpecifier(name="HAL_Value")],
                            classkey="struct",
                        ),
                    ),
                    classes=[
                        ClassScope(
                            class_decl=ClassDecl(
                                typename=PQName(
                                    segments=[AnonymousName(id=1)],
                                    classkey="union",
                                ),
                                access="public",
                            ),
                            fields=[
                                Field(
                                    access="public",
                                    type=Type(
                                        typename=PQName(
                                            segments=[FundamentalSpecifier(name="int")],
                                        ),
                                    ),
                                    name="v_int",
                                ),
                                Field(
                                    access="public",
                                    type=Type(
                                        typename=PQName(
                                            segments=[NameSpecifier(name="HAL_Bool")],
                                        ),
                                    ),
                                    name="v_boolean",
                                ),
                            ],
                        ),
                    ],
                    fields=[
                        Field(
                            access="public",
                            type=Type(
                                typename=PQName(
                                    segments=[AnonymousName(id=1)],
                                    classkey="union",
                                ),
                            ),
                            name="data",
                        ),
                    ],
                ),
            ],
        ),
    )


def test_union_anon_in_struct() -> None:
    content = """
      struct Outer {
        union {
          int x;
          int y;
        };
        int z;
      };
    """
    data = parse_string(content, cleandoc=True)

    assert data == ParsedData(
        namespace=NamespaceScope(
            classes=[
                ClassScope(
                    class_decl=ClassDecl(
                        typename=PQName(
                            segments=[NameSpecifier(name="Outer")],
                            classkey="struct",
                        ),
                    ),
                    classes=[
                        ClassScope(
                            class_decl=ClassDecl(
                                typename=PQName(
                                    segments=[AnonymousName(id=1)],
                                    classkey="union",
                                ),
                                access="public",
                            ),
                            fields=[
                                Field(
                                    access="public",
                                    type=Type(
                                        typename=PQName(
                                            segments=[FundamentalSpecifier(name="int")],
                                        ),
                                    ),
                                    name="x",
                                ),
                                Field(
                                    access="public",
                                    type=Type(
                                        typename=PQName(
                                            segments=[FundamentalSpecifier(name="int")],
                                        ),
                                    ),
                                    name="y",
                                ),
                            ],
                        ),
                    ],
                    fields=[
                        Field(
                            access="public",
                            type=Type(
                                typename=PQName(
                                    segments=[FundamentalSpecifier(name="int")],
                                ),
                            ),
                            name="z",
                        ),
                    ],
                ),
            ],
        ),
    )
