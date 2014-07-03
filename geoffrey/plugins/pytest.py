from difflib import HtmlDiff
import asyncio
import logging
import re
import tempfile

from geoffrey import plugin
from geoffrey.data import EventType
from geoffrey.utils import execute
from geoffrey.subscription import subscription

RESULT_REGEX = re.compile(
    r'^(?P<result>\S)\s'
    r'(?P<file>.*?)::'
    r'(?:(?P<class>.*?)::)?'
    r'(?P<function>.*?)$')

class Pytest(plugin.GeoffreyPlugin):
    """
    pytest plugin.

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modified_files = {}

    @staticmethod
    def parse_result_file(content):
        results = []
        last_message = []
        current_result = None
        for line in content.splitlines():
            match = RESULT_REGEX.match(line)
            if match:
                if current_result is not None:
                    current_result['message'] = '\n'.join(last_message)
                    results.append(current_result)
                    last_message = []
                current_result = match.groupdict()
            else:
                last_message.append(line[1:])  # Message lines have an extra
                                               # space at the beginning

        if current_result is not None:
            current_result['message'] = '\n'.join(last_message)
            results.append(current_result)

        return results

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

            yield from self.hub.put(self.new_event(key="wip_tests_status",
                                               status="running"))

            with tempfile.NamedTemporaryFile(mode="r", encoding="utf-8") as logfile:
                exitcode, stdout, stderr = yield from execute(
                    pytest_path, "-r", "fesxX", "-v",
                    "-m", wip_mark,
                    "--result-log", logfile.name,
                    tests_path)
                details = self.parse_result_file(logfile.file.read())

            if exitcode == 0:
                status = "passed"
            else:
                status = "failed"

            yield from self.hub.put(self.new_event(key="wip_tests_status",
                                                   status=status))

            new_content = event.content or ""
            if last_wip_status != exitcode:
                old_content = self.modified_files.get(event.key, "")
                status_change_filename = event.key
                status_change_differences = HtmlDiff().make_table(
                    old_content.splitlines(), new_content.splitlines(),
                    context=True)
                last_wip_status = exitcode
            self.modified_files[event.key] = new_content

            success = (exitcode == 0)

            state = self.new_state(key="wip_tests", success=success,
                                   filename=status_change_filename,
                                   differences=status_change_differences,
                                   status=status,
                                   details=details)

            yield from self.hub.put(state)
