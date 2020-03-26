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
        variables = {}
        if isinstance(node.value, str):
            filename = node.value
        else:
            mapping = loader.construct_mapping(node, deep=True)
            filename = mapping.get("file")
            variables = mapping.get("variables", {})

        filename = os.path.abspath(os.path.join(os.path.dirname(loader.name), filename))

        try:
            rendered = self._render_templated_yaml(filename, variables)
            return _add_reference(rendered, loader, node)
        except FileNotFoundError as exc:
            _LOGGER.error("Unable to include file %s: %s", filename, exc)
            raise HomeAssistantError(exc)

    def _render_templated_yaml(self, filename, variables={}):
        try:
            template = None
            with open(filename, encoding="utf-8") as file:
                template = Template(file.read(), self.hass)

            template.ensure_valid()

            rendered = template.render({**variables, "_global": self.config.get("variables", {})})
            stream = io.StringIO(rendered)
            stream.name = filename
            return yaml.load(stream, Loader=SafeLineLoader) or OrderedDict()
        except TemplateError as exc:
            _LOGGER.error(str(exc))
            raise HomeAssistantError(exc)
        except yaml.YAMLError as exc:
            _LOGGER.error(str(exc))
            raise HomeAssistantError(exc)
        except UnicodeDecodeError as exc:
            _LOGGER.error("Unable to read file %s: %s", filename, exc)
            raise HomeAssistantError(exc)


constructor = TemplateConstructor()
def setup(hass, config):
    constructor.setup(hass, config.get(DOMAIN))
    SafeLineLoader.add_constructor(constructor.yaml_tag, constructor)
    return True
