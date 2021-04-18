import json

from novel_outliner.core.domain import Novel


def emit_save(novel: Novel):
    with open(novel.config_path, 'w') as outfile:
        json.dump(novel.to_json(), outfile)
