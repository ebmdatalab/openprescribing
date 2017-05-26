from __future__ import print_function

import json
import os

import networkx as nx

from django.conf import settings


class Source(object):
    def __init__(self, name, attrs):
        self.name = name
        self.title = attrs['title']
        self.data_dir = os.path.join(settings.PIPELINE_DATA_BASEDIR, attrs.get('data_dir', name))
        # TODO all the other attributes
        self.tasks = TaskCollection()

    def add_task(self, task):
        self.tasks.add(task)

    def tasks_that_use_raw_source_data(self):
        tasks = self.tasks.by_type('convert')
        if not tasks:
            tasks = self.tasks.by_type('import')
        return tasks


class SourceCollection(object):
    def __init__(self, source_data):
        self._sources = {name: Source(name, attrs) for name, attrs in source_data.items()}

    def __getitem__(self, name):
        return self._sources[name]


class Task(object):
    def __init__(self, name, attrs):
        self.name = name
        self.task_type = attrs['type']
        if self.task_type == 'post_process':
            self.source_id = None
        else:
            self.source_id = attrs['source_id']
        if self.task_type != 'manual_fetch':
            self.command = attrs['command']
        if self.task_type not in ['manual_fetch', 'auto_fetch']:
            self.dependency_names = attrs['dependencies']
        else:
            self.dependency_names = []

    def set_source(self, source):
        self.source = source

    def resolve_dependencies(self, task_collection):
        self.dependencies = [task_collection[name] for name in self.dependency_names]


class ManualFetchTask(Task): pass
class AutoFetchTask(Task): pass
class ConvertTask(Task): pass
class ImportTask(Task): pass
class PostProcessTask(Task): pass


class TaskCollection(object):
    task_type_to_cls = {
        'manual_fetch': ManualFetchTask,
        'auto_fetch': AutoFetchTask,
        'convert': ConvertTask,
        'import': ImportTask,
        'post_process': PostProcessTask,
    }

    def __init__(self, task_data=None, ordered=False, task_type=None):
        self._tasks = {}
        if isinstance(task_data, dict):
            for name, attrs in task_data.items():
                cls = self.task_type_to_cls[attrs['type']]
                task = cls(name, attrs)
                self.add(task)
        elif isinstance(task_data, list):
            for task in task_data:
                self.add(task)
        self._ordered = ordered
        self._type = task_type

    def add(self, task):
        self._tasks[task.name] = task

    def __getitem__(self, name):
        return self._tasks[name]

    def __iter__(self):
        if self._ordered:
            graph = nx.DiGraph()
            for task in self._tasks.values():
                graph.add_node(task)
                for dependency in task.dependencies:
                    graph.add_node(dependency)
                    graph.add_edge(dependency, task)
            tasks = nx.topological_sort(graph)
        else:
            tasks = [task for _, task in sorted(self._tasks.items())]

        for task in tasks:
            if self._type is None:
                yield task
            else:
                if self._type == task.task_type:
                    yield task

    def __nonzero__(self):
        if self._type:
            return any(task for task in self if task.task_type == self._type)
        else:
            return bool(self._tasks)

    def by_type(self, task_type):
        return TaskCollection(list(self), ordered=self._ordered, task_type=task_type)

    def ordered(self):
        return TaskCollection(list(self), ordered=True, task_type=self._type)


def load_tasks():
    metadata_path = settings.PIPELINE_METADATA_DIR

    with open(os.path.join(metadata_path, 'sources.json')) as f:
        source_data = json.load(f)
    sources = SourceCollection(source_data)

    with open(os.path.join(metadata_path, 'tasks.json')) as f:
        task_data = json.load(f)
    tasks = TaskCollection(task_data)

    for task in tasks:
        if task.source_id is None:
            task.set_source(None)
        else:
            source = sources[task.source_id]
            task.set_source(source)
            source.add_task(task)

        task.resolve_dependencies(tasks)

    return tasks
