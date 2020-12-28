"""

The simple parser/collector iterates over the C++ file and returns a data
structure with all elements in it. Not quite as flexible as implementing
your own parser listener, but you can accomplish most things with it.

cxxheaderparser's unit tests predominantly use the simple API for parsing,
so you can expect it to be pretty stable.

"""

import inspect
import typing


from dataclasses import dataclass, field

from .types import (
    ClassDecl,
    EnumDecl,
    Field,
    ForwardDecl,
    FriendDecl,
    Function,
    Method,
    Typedef,
    UsingAlias,
    UsingDecl,
    Variable,
)

from .parserstate import (
    State,
    EmptyBlockState,
    ClassBlockState,
    ExternBlockState,
    NamespaceBlockState,
)
from .parser import CxxParser
from .options import ParserOptions

#
# Data structure
#


@dataclass
class ClassScope:

    class_decl: ClassDecl

    #: Nested classes
    classes: typing.List["ClassScope"] = field(default_factory=list)
    enums: typing.List[EnumDecl] = field(default_factory=list)
    fields: typing.List[Field] = field(default_factory=list)
    friends: typing.List[FriendDecl] = field(default_factory=list)
    methods: typing.List[Method] = field(default_factory=list)
    typedefs: typing.List[Typedef] = field(default_factory=list)

    forward_decls: typing.List[ForwardDecl] = field(default_factory=list)
    using: typing.List[UsingDecl] = field(default_factory=list)
    using_alias: typing.List[UsingAlias] = field(default_factory=list)


@dataclass
class NamespaceScope:

    name: str = ""

    classes: typing.List["ClassScope"] = field(default_factory=list)
    enums: typing.List[EnumDecl] = field(default_factory=list)
    functions: typing.List[Method] = field(default_factory=list)
    typedefs: typing.List[Typedef] = field(default_factory=list)
    variables: typing.List[Variable] = field(default_factory=list)

    forward_decls: typing.List[ForwardDecl] = field(default_factory=list)
    using: typing.List[UsingDecl] = field(default_factory=list)
    using_ns: typing.List[UsingDecl] = field(default_factory=list)
    using_alias: typing.List[UsingAlias] = field(default_factory=list)

    #: Child namespaces
    namespaces: typing.Dict[str, "NamespaceScope"] = field(default_factory=dict)


Block = typing.Union[ClassScope, NamespaceScope]


@dataclass
class Define:
    content: str


@dataclass
class Pragma:
    content: str


@dataclass
class Include:
    #: The filename includes the surrounding ``<>`` or ``"``
    filename: str


@dataclass
class UsingNamespace:
    ns: str


@dataclass
class ParsedData:

    namespace: NamespaceScope = field(default_factory=lambda: NamespaceScope())

    defines: typing.List[Define] = field(default_factory=list)
    pragmas: typing.List[Pragma] = field(default_factory=list)
    includes: typing.List[Include] = field(default_factory=list)


#
# Visitor implementation
#


class SimpleCxxVisitor:
    """
    A simple visitor that stores all of the C++ elements passed to it
    in an "easy" to use data structure

    .. warning:: Names are not resolved, so items are stored in the scope that
                 they are found. For example:

                 .. code-block:: c++

                    namespace N {
                        class C;
                    }

                    class N::C {
                        void fn();
                    };

                The 'C' class would be a forward declaration in the 'N' namespace,
                but the ClassDecl for 'C' would be stored in the global
                namespace instead of the 'N' namespace.
    """

    data: ParsedData
    namespace: NamespaceScope
    block: Block

    def __init__(self):
        self.namespace = NamespaceScope("")
        self.block = self.namespace

        self.ns_stack = typing.Deque[NamespaceScope]()
        self.block_stack = typing.Deque[Block]()

        self.data = ParsedData(self.namespace)

    def on_define(self, state: State, content: str) -> None:
        self.data.defines.append(Define(content))

    def on_pragma(self, state: State, content: str) -> None:
        self.data.pragmas.append(Pragma(content))

    def on_include(self, state: State, filename: str) -> None:
        self.data.includes.append(Include(filename))

    def on_empty_block_start(self, state: EmptyBlockState) -> None:
        # this matters for some scope/resolving purposes, but you're
        # probably going to want to use clang if you care about that
        # level of detail
        pass

    def on_empty_block_end(self, state: EmptyBlockState) -> None:
        pass

    def on_extern_block_start(self, state: ExternBlockState) -> None:
        pass  # TODO

    def on_extern_block_end(self, state: ExternBlockState) -> None:
        pass

    def on_namespace_start(self, state: NamespaceBlockState) -> None:
        parent_ns = self.namespace
        self.block_stack.append(parent_ns)
        self.ns_stack.append(parent_ns)

        ns = None
        names = state.namespace.names
        if not names:
            # all anonymous namespaces in a translation unit are the same
            names = [""]

        for name in names:
            ns = parent_ns.namespaces.get(name)
            if ns is None:
                ns = NamespaceScope(name)
                parent_ns.namespaces[name] = ns
            parent_ns = ns

        self.block = ns
        self.namespace = ns

    def on_namespace_end(self, state: NamespaceBlockState) -> None:
        self.block = self.block_stack.pop()
        self.namespace = self.ns_stack.pop()

    def on_forward_decl(self, state: State, fdecl: ForwardDecl) -> None:
        self.block.forward_decls.append(fdecl)

    def on_variable(self, state: State, v: Variable) -> None:
        self.block.variables.append(v)

    def on_function(self, state: State, fn: Function) -> None:
        self.block.functions.append(fn)

    def on_typedef(self, state: State, typedef: Typedef) -> None:
        self.block.typedefs.append(typedef)

    def on_using_namespace(self, state: State, namespace: typing.List[str]) -> None:
        ns = UsingNamespace("::".join(namespace))
        self.block.using_ns.append(ns)

    def on_using_alias(self, state: State, using: UsingAlias):
        self.block.using_alias.append(using)

    def on_using_declaration(self, state: State, using: UsingDecl) -> None:
        self.block.using.append(using)

    #
    # Enums
    #

    def on_enum(self, state: State, enum: EnumDecl) -> None:
        self.block.enums.append(enum)

    #
    # Class/union/struct
    #

    def on_class_start(self, state: ClassBlockState) -> None:
        block = ClassScope(state.class_decl)
        self.block.classes.append(block)
        self.block_stack.append(self.block)
        self.block = block

    def on_class_field(self, state: State, f: Field) -> None:
        self.block.fields.append(f)

    def on_class_method(self, state: ClassBlockState, method: Method) -> None:
        self.block.methods.append(method)

    def on_class_friend(self, state: ClassBlockState, friend: FriendDecl):
        self.block.friends.append(friend)

    def on_class_end(self, state: ClassBlockState) -> None:
        self.block = self.block_stack.pop()


def parse_string(
    content: str,
    *,
    filename="<str>",
    options: typing.Optional[ParserOptions] = None,
    cleandoc: bool = False,
) -> ParsedData:
    """
    Simple function to parse a header and return a data structure
    """
    if cleandoc:
        content = inspect.cleandoc(content)

    visitor = SimpleCxxVisitor()
    parser = CxxParser(filename, content, visitor, options)
    parser.parse()

    return visitor.data


def parse_file(
    filename: str,
    encoding: typing.Optional[str] = None,
    *,
    options: typing.Optional[ParserOptions] = None,
) -> ParsedData:
    """
    Simple function to parse a header from a file and return a data structure
    """

    with open(filename, encoding=encoding) as fp:
        content = fp.read()

    return parse_string(content, filename=filename, options=options)