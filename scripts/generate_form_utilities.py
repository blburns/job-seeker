import yaml
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'form-utilities.config.yaml')
CSS_OUT_ALL = os.path.join(os.path.dirname(__file__), '../app/static/css/form-utilities.css')
CSS_OUT_THEME = os.path.join(os.path.dirname(__file__), '../app/static/css/theme-form-utilities.css')

# Utility class templates
TEMPLATES = {
    'input-bg': '.input-bg-{color}-{shade} {{ background-color: var(--{color}-{shade}) !important; }}',
    'input-text': '.input-text-{color}-{shade} {{ color: var(--{color}-{shade}) !important; }}',
    'input-border': '.input-border-{color}-{shade} {{ border-color: var(--{color}-{shade}) !important; }}',
    'label': '.label-{color}-{shade}, .form-label.label-{color}-{shade} {{ color: var(--{color}-{shade}) !important; }}',
    'form-text': '.form-text-{color}-{shade} {{ color: var(--{color}-{shade}) !important; }}',
    'input-group-text': '.input-group-text-{color}-{shade} {{ background-color: var(--{color}-{shade}) !important; color: var(--{color}-900) !important; }}',
    'select-bg': '.select-bg-{color}-{shade} {{ background-color: var(--{color}-{shade}) !important; }}',
    'select-text': '.select-text-{color}-{shade} {{ color: var(--{color}-{shade}) !important; }}',
    'check-bg': '.check-bg-{color}-{shade} {{ background-color: var(--{color}-{shade}) !important; }}',
    'check-border': '.check-border-{color}-{shade} {{ border-color: var(--{color}-{shade}) !important; }}',
    'range-track': '.range-track-{color}-{shade} {{ background-color: var(--{color}-{shade}) !important; }}',
    'range-thumb': '.range-thumb-{color}-{shade} {{ background-color: var(--{color}-{shade}) !important; }}',
    'file-upload-bg': '.file-upload-bg-{color}-{shade} {{ background-color: var(--{color}-{shade}) !important; }}',
    'file-upload-text': '.file-upload-text-{color}-{shade} {{ color: var(--{color}-{shade}) !important; }}',
    'valid-feedback': '.valid-feedback-{color}-{shade} {{ color: var(--{color}-{shade}) !important; }}',
    'invalid-feedback': '.invalid-feedback-{color}-{shade} {{ color: var(--{color}-{shade}) !important; }}',
    'legend': '.legend-{color}-{shade} {{ color: var(--{color}-{shade}) !important; }}',
    'output-bg': '.output-bg-{color}-{shade} {{ background-color: var(--{color}-{shade}) !important; }}',
    'progress-bar-bg': '.progress-bar-bg-{color}-{shade} {{ background-color: var(--{color}-{shade}) !important; }}',
}

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)

def generate_all_utilities(config):
    lines = [
        '/* Generated form color utilities: all combinations */',
        '/* Do not edit by hand. Edit form-utilities.config.yaml and rerun the generator. */',
        '',
    ]
    for util, enabled in config['utilities'].items():
        if not enabled:
            continue
        for color in config['color_scales']:
            for shade in config['shades']:
                lines.append(TEMPLATES[util].format(color=color, shade=shade))
    return '\n'.join(lines)

def generate_theme_utilities(config):
    lines = [
        '/* Generated form color utilities: theme selection only */',
        '/* Do not edit by hand. Edit form-utilities.config.yaml and rerun the generator. */',
        '',
    ]
    for class_name in config.get('theme_includes', []):
        # Try to parse the class_name to match a template
        for util in TEMPLATES:
            prefix = util.replace('_', '-')
            if class_name.startswith(prefix):
                # Extract color and shade
                try:
                    _, color, shade = class_name.split('-')
                except ValueError:
                    continue
                lines.append(TEMPLATES[util].format(color=color, shade=shade))
                break
    return '\n'.join(lines)

def main():
    config = load_config()
    all_css = generate_all_utilities(config)
    theme_css = generate_theme_utilities(config)
    with open(CSS_OUT_ALL, 'w') as f:
        f.write(all_css + '\n')
    with open(CSS_OUT_THEME, 'w') as f:
        f.write(theme_css + '\n')
    print(f"Wrote {CSS_OUT_ALL} and {CSS_OUT_THEME}")

if __name__ == '__main__':
    main() 