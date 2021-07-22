import os

from src.main.python.plotlyst.core.client import context, LATEST
from src.main.python.plotlyst.test.conftest import init_db

context.init('resources')
init_db()
os.rename('resources/novels.sqlite', f'resources/rev-{LATEST.value}.sqlite')
