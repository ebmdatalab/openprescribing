from django.test import TestCase

from pipeline.runner import load_tasks


class PipelineTests(TestCase):
    def setUp(self):
        self.tasks = load_tasks()

    def test_task_initialisation(self):
        task = self.tasks['fetch_source_a']
        self.assertEqual(task.name, 'fetch_source_a')
        self.assertEqual(task.task_type, 'manual_fetch')
        self.assertEqual(task.source_id, 'source_a')
        self.assertEqual(task.dependencies, [])

        task = self.tasks['convert_source_a']
        self.assertEqual(task.dependency_names, ['fetch_source_a'])

    def test_tasks_by_type(self):
        tasks = self.tasks.by_type('manual_fetch')
        self.assertIn('fetch_source_a', [task.name for task in tasks])

        tasks = self.tasks.by_type('auto_fetch')
        self.assertIn('fetch_source_b', [task.name for task in tasks])

    def test_tasks_ordered(self):
        task_names = [task.name for task in self.tasks.ordered()]
        for name1, name2 in [
            ['fetch_source_a', 'convert_source_a'],
            ['convert_source_a', 'import_source_a'],
            ['fetch_source_b', 'import_source_b'],
            ['import_source_a', 'import_source_b'],
            ['fetch_source_c', 'import_source_c1'],
            ['import_source_a', 'import_source_c1'],
            ['import_source_b', 'import_source_c1'],
            ['fetch_source_c', 'import_source_c2'],
            ['import_source_c1', 'import_source_c2'],
            ['import_source_a', 'post_process'],
            ['import_source_b', 'post_process'],
            ['import_source_c1', 'post_process'],
        ]:
            self.assertTrue(task_names.index(name1) < task_names.index(name2))

    def test_tasks_by_type_ordered(self):
        task_names = [task.name for task in self.tasks.by_type('import').ordered()]
        expected_output = [
            'import_source_a',
            'import_source_b',
            'import_source_c1',
            'import_source_c2',
        ]
        self.assertEqual(task_names, expected_output)

    def test_tasks_ordered_by_type(self):
        task_names = [task.name for task in self.tasks.ordered().by_type('import')]
        expected_output = [
            'import_source_a',
            'import_source_b',
            'import_source_c1',
            'import_source_c2',
        ]
        self.assertEqual(task_names, expected_output)

    def test_source_initialisation(self):
        source = self.tasks['import_source_a'].source
        self.assertEqual(source.name, 'source_a')
        self.assertEqual(source.title, 'Source A')
