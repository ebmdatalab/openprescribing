from __future__ import print_function

from collections import OrderedDict
import json

import networkx as nx

with open('metadata/manifest.json') as f:
    sources = json.load(f)

print('There are {} sources'.format(len(sources)))

keys = [
    'id',
    'type',
    'source',
    'command',
    'dependencies',
]

tasks = []

for source in sources:
    source_id = source['id']

    manual_fetcher = False
    fetcher = source.get('fetcher')
    if fetcher:
        tasks.append({
            'id': 'fetch_{}'.format(source_id),
            'source': source_id,
            'type': 'auto_fetch',
            'command': fetcher,
            'dependencies': [],
        })
    elif 'core_data' in source['tags'] and source.get('publisher'):
        manual_fetcher = True
        tasks.append({
            'id': 'fetch_{}'.format(source_id),
            'source': source_id,
            'type': 'manual_fetch',
            'dependencies': [],
        })

    before_tasks = []
    before_import = source.get('before_import', [])
    if len(before_import) == 1:
        assert source['publisher'] == ''
        before_tasks.append({
            'id': source_id,
            'type': 'post_process',
            'command': before_import[0],
            'dependencies': source.get('depends_on', []),
        })
    else:
        for ix, command in enumerate(before_import):
            assert source['publisher'] == ''
            before_tasks.append({
                'id': '{}_{}'.format(source_id, ix),
                'type': 'post_process',
                'command': command,
                'dependencies': source.get('depends_on', []) + [task['id'] for task in before_tasks],
            })

    tasks.extend(before_tasks)

    importer_dependencies = []
    if fetcher or manual_fetcher:
        importer_dependencies.append('fetch_{}'.format(source_id))

    if before_tasks:
        importer_dependencies.extend(before_tasks)
    else:
        importer_dependencies.extend(source.get('depends_on', []))

    importers = source.get('importers', [])
    if len(importers) == 1:
        importer_id = 'import_{}'.format(source_id)
        tasks.append({
            'id': importer_id,
            'source': source_id,
            'type': 'import',
            'command': importers[0],
            'dependencies': importer_dependencies,
        })
        importer_ids = [importer_id]
    else:
        importer_ids = []
        for ix, importer in enumerate(importers):
            importer_id = 'import_{}_{}'.format(source_id, ix)
            tasks.append({
                'id': importer_id,
                'source': source_id,
                'type': 'import',
                'command': importer,
                'dependencies': importer_dependencies + importer_ids[::],
            })
            importer_ids.append(importer_id)

    if importers:
        tasks.append({
            'id': source_id,
            'source': source_id,
            'type': 'dummy',
            'dependencies': importer_ids,
        })

task_ids = [task['id'] for task in tasks]

for task in tasks:
    if task['type'] == 'dummy':
        for task1 in tasks:
            if task['id'] in task1['dependencies']:
                task1['dependencies'].remove(task['id'])
                task1['dependencies'].extend(task['dependencies'])

tasks = [task for task in tasks if task['type'] != 'dummy']

for task in tasks:
    for dependency_id in task['dependencies']:
        assert dependency_id in task_ids, 'Unknown dependency: {}'.format(dependency_id)

graph = nx.DiGraph()
for task in tasks:
    graph.add_node(task['id'])
    for dependency in task['dependencies']:
        graph.add_node(dependency)
        graph.add_edge(dependency, task['id'])

ordered_task_ids = nx.topological_sort(graph)
tasks = sorted(tasks, key=lambda t: ordered_task_ids.index(t['id']))

tasks_for_dump = []

for task in tasks:
    if not task['dependencies']:
        del task['dependencies']

    task = OrderedDict([[k, task[k]] for k in keys if task.get(k)])
    tasks_for_dump.append(task)

with open('metadata/tasks.json', 'w') as f:
    json.dump(tasks_for_dump, f, indent=4)
