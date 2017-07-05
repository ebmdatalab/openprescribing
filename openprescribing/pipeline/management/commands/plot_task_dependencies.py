import json
import os

from graphviz import Digraph

from django.conf import settings
from django.core.management import BaseCommand

from ...runner import load_tasks


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        tasks = load_tasks()

        graph = Digraph('dependencies', format='svg')

        task_type_to_colour = {
            'manual_fetch': '#ffaaaa',
            'auto_fetch': '#ffaacc',
            'import': '#aaffaa',
            'convert': '#aaaaff',
            'post_process': '#aaffff',
        }

        for task in tasks:
            colour = task_type_to_colour[task.task_type]
            graph.node(task.name, style='filled', fillcolor=colour)
            for dependency_name in task.dependency_names:
                graph.edge(dependency_name, task.name)

        graph.render('dependencies', cleanup=True)
