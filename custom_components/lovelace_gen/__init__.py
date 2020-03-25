import os
import logging
import json
import io
import time
from collections import OrderedDict

import jinja2
import yaml

from homeassistant.util.yaml.loader import _add_reference, SafeLineLoader
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

jinja = jinja2.Environment(loader=jinja2.FileSystemLoader("/"))

global_variables = {}

def _render_templated_yaml(file_name, variables={}):
    try:
        template = jinja.get_template(file_name)
        rendered = template.render({**variables, "_global": global_variables})
        stream = io.StringIO(rendered)
        stream.name = file_name
        return yaml.load(stream, Loader=SafeLineLoader) or OrderedDict()
    except yaml.YAMLError as exc:
        _LOGGER.error(str(exc))
        raise HomeAssistantError(exc)
    except UnicodeDecodeError as exc:
        _LOGGER.error("Unable to read file %s: %s", file_name, exc)
        raise HomeAssistantError(exc)


def _include_templated_yaml(loader, node):
    variables = {}
    if isinstance(node.value, str):
        file_name = node.value
    else:
        mapping = loader.construct_mapping(node, deep=True)
        file_name = mapping.get("file")
        variables = mapping.get("variables", {})

    file_name = os.path.abspath(os.path.join(os.path.dirname(loader.name), file_name))

    try:
        rendered = _render_templated_yaml(file_name, variables)
        return _add_reference(rendered, loader, node)
    except FileNotFoundError as exc:
        _LOGGER.error("Unable to include file %s: %s", file_name, exc)
        raise HomeAssistantError(exc)

SafeLineLoader.add_constructor("!template", _include_templated_yaml)

async def async_setup(hass, config):
    global_variables.update(config.get("lovelace_preprocessor"))
    return True
