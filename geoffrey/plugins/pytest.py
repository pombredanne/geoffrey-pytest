import logging
import asyncio

from geoffrey import plugin
from geoffrey.data import EventType
from geoffrey.utils import execute
from geoffrey.subscription import subscription


class Pytest(plugin.GeoffreyPlugin):
    """
    pytest plugin.

    """
    @subscription
    def modified_pyfiles(self, event):
        """
        Modified python files.

        """
        return (self.project.name == event.project and
                event.plugin == "filecontent" and
                event.key.endswith('.py') and
                event.type in (EventType.created, EventType.modified))

    @asyncio.coroutine
    def wip_tests(self, events:"modified_pyfiles") -> plugin.Task:
        """
        Run tests marked with @wip tag.

        """
        pytest_path = self.config.get(self._section_name, "pytest_path")
        tests_path = self.config.get(self._section_name, "tests_path")
        wip_mark = self.config.get(self._section_name, "wip_mark")

        last_wip_status = None
        status_change_filename = None
        status_change_differences = None

        while True:
            event = yield from events.get()

            exitcode, stdout, stderr = yield from execute(
                pytest_path, "-r", "fesxX", "-v", "-m", wip_mark, tests_path)

            log_event = self.new_event(key="wip_tests_log", status=exitcode,
                                       stdout=stdout, stderr=stderr)
            yield from self.hub.put(log_event)

            if last_wip_status != exitcode:
                status_change_filename = event.key
                status_change_differences = event.differences
                last_wip_status = exitcode

            success = (exitcode==0)

            state = self.new_state(key="wip_tests", success=success,
                                   filename=status_change_filename,
                                   differences=status_change_differences)
            yield from self.hub.put(state)
