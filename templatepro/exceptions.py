"""Module containing the exception class for templatepro."""


class TemplateError(Exception):
    """Use to capture error template construction."""


class TemplateParsedLineError(TemplateError):
    """Use to capture error parsed line for template builder."""


class TemplateBuilderError(TemplateError):
    """Use to capture error template construction."""


class TemplateBuilderInvalidFormat(TemplateError):
    """Use to capture error if user_data has invalid format."""
