import os

from src.main.python.plotlyst.core.client import context, LATEST
from src.main.python.plotlyst.test.conftest import init_project

context.init('resources')
init_project()
os.rename('resources/novels.sqlite', f'resources/rev-{LATEST.value}.sqlite')
