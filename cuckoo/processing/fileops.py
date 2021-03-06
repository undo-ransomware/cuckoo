# Copyright (C) 2019 Cuckoo Foundation.
# This file is part of Cuckoo Sandbox - http://www.cuckoosandbox.org
# See the file 'docs/LICENSE' for copying permission.

from cuckoo.common.exceptions import CuckooProcessingError
from cuckoo.processing.behavior import BehaviorAnalysis
from .platform.windows import WindowsMonitor

class FileOps(BehaviorAnalysis):
	"""Logs a single, unified time series of all file operations.

	This omits all operations that wouldn't be visible to a cloud storage
	service, such as reading from files.
	"""

	enabled = True
	key = "fileops"

	def run(self):
		"""Run analysis.
		@return: results list.
		"""

		parser = WindowsMonitor(self, task_id=self.task["id"])
		events = dict()
		for path in self._enum_logs():
			for event in parser.parse(path):
				if event["type"] == "generic":
					cat = event["category"]
					if cat.startswith("file_") or cat.startswith("directory_"):
						time = event["ts"]
						if time not in events:
							events[time] = []
						events[time].append(event)

		ops = []
		prev = None
		for time in sorted(events.keys()):
			for event in events[time]:
				cat = event["category"]
				path = event["value"]
				if hasattr(self, "handle_%s" % cat):
					op = getattr(self, "handle_%s" % cat)(cat, path)
					if op is not None:
						op["time"] = event["ts"]
						if op != prev:
							ops.append(op)
							prev = op
				else:
					raise CuckooProcessingError("cannot handle " + cat)
		return ops

	def single(self, op, path):
		return { "op": op, "path": path }

	handle_directory_created = single
	handle_directory_removed = single
	handle_file_created = single
	handle_file_written = single
	handle_file_deleted = single
	# difference from opening and writing is a different creation timestamp.
	# unlikely to matter, but let's not drop that information here; it is
	# visible in the post-analysis snapshot after all.
	handle_file_recreated = single

	def from_to(self, op, paths):
		return { "op": op, "from": paths[0], "to": paths[1] }

	handle_file_moved = from_to
	handle_file_copied = from_to

	def ignore(self, op, path):
		return None

	# read operations are invisible on cloud storage
	handle_directory_enumerated = ignore
	handle_file_read = ignore
	handle_file_exists = ignore
	# open for write might be visible, but we'll see that write later anyway
	handle_file_opened = ignore
	# idiot programmer? these are quite common ;)
	handle_file_failed = ignore
