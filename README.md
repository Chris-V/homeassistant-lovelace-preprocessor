lovelace\_preprocessor
============

Adds Jinja support to the lovelace yaml parser for Home Assistant.

This is based off [lovelace_gen](https://github.com/thomasloven/hass-lovelace_gen). As a matter of personal preference I prefer having template inclusions to be explicit. This also avoids overriding core features, but instead adding to them.

# Installation instructions

- Copy the contents of `custom_components/lovelace_preprocessor/` to `<your config dir>/custom_components/lovelace_preprocessor/`.
- Add the following to your `configuration.yaml`:

```yaml
lovelace_preprocessor:

lovelace:
  mode: yaml
```

- Restart Home Assistant

# Usage

This integration changes the way Home Assistant parses your `ui_lovelace.yaml` before sending the information off to the lovelace frontend in your browser. It's obviously only useful if you are using [YAML mode](https://www.home-assistant.io/lovelace/yaml-mode/).

### First of all
To rerender the frontend, use the Refresh option from the three-dots-menu in Lovelace

![refresh](https://user-images.githubusercontent.com/1299821/62565489-2e655780-b887-11e9-86a1-2de868a4dc7d.png)

### Second of all

Any yaml file that is to be processed with `lovelace_preprocessor` *MUST* be included with the `!template` tag.

The `!template` tag can either accept a file name or a dictionary with the keys `file` and `variables`. This allows reusing templated files with different variables.

## Exemples

```yaml
type: horizontal-stack
cards:
  - !template main_light.yaml
  - !template
      file: button_card.yaml
      variables:
        entity: light.ceiling_lights
        name: LIGHT!
```

`button_card.yaml`
```yaml
{% if entity.startswith("light") %}
type: light
{% else %}
type: entity-button
{% endif %}
entity: {{ entity }}
name: {{ name }}
```
