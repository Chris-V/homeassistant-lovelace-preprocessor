import os
import logging
import io
from collections import OrderedDict

import yaml

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.template import Template, TemplateError
from homeassistant.util.yaml.loader import _add_reference, SafeLineLoader

DOMAIN = "lovelace_preprocessor"
_LOGGER = logging.getLogger(__name__)

class TemplateConstructor(object):
    hass = None
    config = {}
    yaml_tag = '!template'

    def setup(self, hass, config):
        self.hass = hass
        self.config.update(config)

    def __call__(self, loader, node):
        filename, variables = self._read_tag(loader, node)
        stream = self._render_template(filename, variables)

        try:
            document = yaml.load(stream, SafeLineLoader) or OrderedDict()
            return _add_reference(document, loader, node)
        except yaml.YAMLError as ex:
            _LOGGER.error("Unable to parse rendered YAML in %s: %s", filename, ex)
            raise HomeAssistantError(exc)

    def _read_tag(self, loader, node):
        if isinstance(node, yaml.ScalarNode):
            filename = node.value
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

            rendered = template.render({**variables, "_global": self.config.get("variables", {})})
            stream = io.StringIO(rendered)
            stream.name = filename
            return stream
        except (FileNotFoundError, UnicodeDecodeError) as ex:
            _LOGGER.error("Unable to read file %s: %s", filename, ex)
            raise HomeAssistantError(ex)
        except TemplateError as ex:
            _LOGGER.error("Unable to render file %s: %s", filename, ex)
            raise HomeAssistantError(ex)


constructor = TemplateConstructor()
def setup(hass, config):
    constructor.setup(hass, config.get(DOMAIN))
    yaml.SafeLoader.add_constructor(constructor.yaml_tag, constructor)
    return True
