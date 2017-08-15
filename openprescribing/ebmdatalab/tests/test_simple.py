import pytest
import mock
from mock import patch
from mock import MagicMock
from ebmdatalab import bigquery


def test_get_env_setting_raises():
    from ebmdatalab import bigquery
    with pytest.raises(StandardError):
        bigquery.get_env_setting('FROB1234')


def test_get_env_setting_default():
    result = bigquery.get_env_setting('FROB1234', 'foo')
    assert result == 'foo'


def test_get_bq_service():
    import os
    old_env = os.environ.copy()
    if 'GOOGLE_APPLICATION_CREDENTIALS' in old_env:
        del(old_env['GOOGLE_APPLICATION_CREDENTIALS'])
    env = patch.dict('os.environ', old_env, clear=True)
    with env:
        service = bigquery.get_bq_service()
        assert service.projects().list().body is None


@patch('ebmdatalab.bigquery.bigquery')
@patch('ebmdatalab.bigquery.wait_for_job')
def test_load_data_from_file(wait_mock, bigquery_mock):
    with patch('tempfile.NamedTemporaryFile', create=True) as mock_tempfile:
        writer_under_test = MagicMock(spec=file)
        mock_tempfile.return_value = writer_under_test
        with patch('ebmdatalab.bigquery.open', create=True) as mock_inputfile:
            mock_csv = MagicMock(spec=file)
            mock_csv.__enter__.return_value = iter(["1,foo", "2,bar"])
            mock_inputfile.return_value = mock_csv
            bigquery.load_data_from_file(
                'dataset', 'table', 'source_mock',
                [], _transform=lambda row: [row[0], row[1].upper()])
            # Check we read the passed-in filename
            mock_inputfile.assert_called_once_with('source_mock', 'rb')
            # Check the writer was called with transformed values
            write_under_test = writer_under_test.__enter__.return_value.write
            write_under_test.assert_any_call('1,FOO\r\n')
            write_under_test.assert_any_call('2,BAR\r\n')
            # Check bigquery `upload_from_file` was called
            dataset = bigquery_mock.Client.return_value.dataset.return_value
            assert dataset.table.return_value.upload_from_file.called


@patch('ebmdatalab.bigquery.bigquery')
@patch('ebmdatalab.bigquery.wait_for_job')
def test_load_data_from_file_with_exception(wait_mock, bigquery_mock):
    with patch('tempfile.NamedTemporaryFile', create=True) \
            as mock_tempfile:
        writer_under_test = MagicMock(spec=file)
        mock_tempfile.return_value = writer_under_test
        with patch('ebmdatalab.bigquery.open', create=True) as mock_inputfile:
            mock_csv = MagicMock(spec=file)
            mock_csv.__enter__.return_value = iter(["1,foo", "2,bar"])
            mock_inputfile.return_value = mock_csv
            wait_mock.side_effect = RuntimeError(["foo"])
            with patch('shutil.copyfile'):
                with pytest.raises(RuntimeError) as e_info:
                    bigquery.load_data_from_file(
                        'dataset', 'table', 'source_mock',
                        [], _transform=lambda row: [row[0], row[1].upper()])
                assert "Failed CSV has been copied" in e_info.exconly()


@patch('ebmdatalab.bigquery.get_env_setting')
@patch('ebmdatalab.bigquery.load_data_from_file')
@patch('psycopg2.connect')
def test_load_data_from_pg(mock_connection, *args):
    bigquery.load_data_from_pg(
        'dataset', 'table', 'pg_table', [], cols=['a', 'b'])
    copy_expert = mock_connection.return_value.cursor.return_value.copy_expert
    copy_expert.assert_any_call(
        "COPY pg_table(a,b) TO STDOUT (FORMAT CSV, NULL '')",
        mock.ANY)
