from typing import Any, Dict, Type

from cattr.converters import Converter
from gherkin.errors import ParserError
from gherkin.parser import Parser

from .ast_node.gherkin_document import GherkinDocument
from .errors import DeserializeError, InvalidInput
from .utils import camel_to_snake_case, strip_spaces


class CustomConverter(Converter):
    def structure_attrs_fromdict(self, obj: Dict[str, Any], cls: Type) -> Any:
        # Make sure the type in the parsed object matches the class we use
        # to structure the object
        if "type" in obj:
            type_name = obj.pop("type")
            cls_name = cls.__name__
            assert type_name == cls_name, f"{type_name} does not match {cls_name}"

        # Note that keys are in camelCase convention, for example, tableHeader,
        # tableBody. Therefore, we need to convert the keys to snake_case.
        transformed_obj = {}
        for key, value in obj.items():
            if isinstance(value, str):
                # For some types of node, the indentation of the lines is included
                # in the value of such nodes. Then the indentation can be changed after
                # formatting. Therefore, we need to strips spaces around each line of
                # the value here for consistent results. This also removes trailing
                # spaces.
                value = strip_spaces(value)

            transformed_obj[camel_to_snake_case(key)] = value

        return super(CustomConverter, self).structure_attrs_fromdict(
            transformed_obj, cls
        )


converter = CustomConverter()


def parse(content: str) -> GherkinDocument:
    """
    Parse the content of a file to an AST.
    """
    parser = Parser()

    try:
        parse_result = parser.parse(content)
    except ParserError as e:
        raise InvalidInput(e) from e

    try:
        result = converter.structure(parse_result, GherkinDocument)
    except Exception as e:  # pragma: no cover
        raise DeserializeError(f"{e.__class__.__name__}: {e}") from e

    return result
