from collections import OrderedDict
import io
import logging
import os
import re
import yaml

from annotatedyaml.loader import add_constructor, _add_reference, PythonSafeLoader
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.template import Template, TemplateError

DOMAIN = "lovelace_preprocessor"
TAG = "!template"
_LOGGER = logging.getLogger(__name__)

class TemplateConstructor(object):
    hass = None
    config = {}

    yaml_template_matcher = re.compile(r".*\.ya?ml(\.j2)?", re.IGNORECASE)

    def __init__(self, hass, config):
        self.hass = hass
        self.config.update(config)

    def __call__(self, loader, node):
        filename, variables = self._read_tag(loader, node)
        stream = self._render_template(filename, variables)
        stream.seek(0)

        try:
            if self.yaml_template_matcher.match(filename):
                sub_loader = lambda _stream: PythonSafeLoader(_stream, loader.secrets)
                document = yaml.load(stream, Loader=sub_loader)
                return _add_reference(document, loader, node)
            else:
                return _add_reference(stream.read(), loader, node)
        except yaml.YAMLError as ex:
            _LOGGER.error("Unable to parse rendered YAML in %s: %s", filename, ex)
            raise HomeAssistantError(ex) from ex

    def _read_tag(self, loader, node):
        if isinstance(node, yaml.ScalarNode):
            filhename = node.value
            variables = {}
        else:
            mapping = loader.construct_mapping(node, deep=True)
            filename = mapping.get("file")
            variables = mapping.get("variables", {})

        filename = os.path.abspath(os.path.join(os.path.dirname(loader.name), filename))
        return filename, variables

    def _render_template(self, filename, variables):
        try:
            template = None
            with open(filename, encoding="utf-8") as file:
                template = Template(file.read(), self.hass)

            template.ensure_valid()

            rendered = template.render(
                variables = {**variables, "_global": self.config.get("variables", {})},
                limited = True,
            )
            stream = io.StringIO(rendered)
            stream.name = filename
            return stream
        except (FileNotFoundError, UnicodeDecodeError) as ex:
            _LOGGER.error("Unable to read file %s: %s", filename, ex)
            raise HomeAssistantError(ex) from ex
        except TemplateError as ex:
            _LOGGER.error("Unable to render file %s: %s", filename, ex)
            raise HomeAssistantError(ex) from ex


def setup(hass, config):
    constructor = TemplateConstructor(hass, config.get(DOMAIN))
    add_constructor(TAG, constructor)
    return True
