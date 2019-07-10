# Copyright (C) 2019 Cuckoo Foundation.
# This file is part of Cuckoo Sandbox - http://www.cuckoosandbox.org
# See the file 'docs/LICENSE' for copying permission.

from .platform.windows import WindowsMonitor

from cuckoo.processing.behavior import BehaviorAnalysis

class FileOps(BehaviorAnalysis):
	"""Logs a time series of all file operations.

	This includes operations that wouldn't be visible to a cloud storage service,
	such as files being written.
	"""

	enabled = True
	key = "fileops"

	def run(self):
		"""Run analysis.
		@return: results dict.
		"""

		parser = WindowsMonitor(self, task_id=self.task["id"])
		log = []
		for path in self._enum_logs():
			for event in parser.parse(path):
				if event["type"] == "generic":
					category = event["category"]
					if category.startswith("file_"):
						entry = {
							"time": event["time"],
							"event": category[5:]
						}
						if hasattr(self, "handle_%s" % category):
							getattr(self, "handle_%s" % category)(entry, event)
						else:
							entry["name"] = event["value"]
						log.append(entry)
		return log

	def handle_file_moved(self, entry, event):
		entry["name"] = event["value"][1]
		entry["old_name"] = event["value"][0]

	def handle_file_copied(self, entry, event):
		entry["name"] = event["value"][1]
		entry["old_name"] = event["value"][0]
