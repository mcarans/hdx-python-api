# -*- coding: UTF-8 -*-
"""Dataset Tests (noncore methods)"""
import copy
import datetime
import json
from os.path import join

import pytest
from parser import ParserError

from hdx.location.country import Country
from hdx.utilities.compare import assert_files_same
from hdx.utilities.dateparse import parse_date_range
from hdx.utilities.downloader import Download
from hdx.utilities.path import temp_dir

from hdx.data.organization import Organization
from hdx.data.user import User
from hdx.data.vocabulary import Vocabulary
from . import dataset_data, resources_data, user_data, organization_data, resulttags, resultgroups
from . import MockResponse, dataset_mockshow
from hdx.data.dataset import Dataset
from hdx.data.hdxobject import HDXError

from hdx.hdx_configuration import Configuration
from .test_organization import organization_mockshow
from .test_resource_view import resource_view_list, resource_view_mockshow, resource_view_mocklist, \
    resource_view_mockcreate
from .test_showcase import showcase_resultdict
from .test_user import user_mockshow
from .test_vocabulary import vocabulary_mockshow


class TestDatasetNoncore:
    association = None
    url = 'https://raw.githubusercontent.com/OCHA-DAP/hdx-python-api/master/tests/fixtures/test_data.csv'
    hxltags = {'EVENT_ID_CNTY': '#event+code', 'EVENT_DATE': '#date+occurred', 'YEAR': '#date+year',
               'EVENT_TYPE': '#event+type', 'ACTOR1': '#group+name+first', 'ASSOC_ACTOR_1':
                   '#group+name+first+assoc', 'ACTOR2': '#group+name+second', 'ASSOC_ACTOR_2':
                   '#group+name+second+assoc', 'REGION': '#region+name', 'COUNTRY': '#country+name',
               'ADMIN1': '#adm1+name', 'ADMIN2': '#adm2+name', 'ADMIN3': '#adm3+name', 'LOCATION': '#loc+name',
               'LATITUDE': '#geo+lat', 'LONGITUDE': '#geo+lon', 'SOURCE': '#meta+source', 'NOTES':
                   '#description', 'FATALITIES': '#affected+killed', 'ISO3': '#country+code'}

    @pytest.fixture(scope='class')
    def static_resource_view_yaml(self):
        return join('tests', 'fixtures', 'config', 'hdx_resource_view_static.yml')

    @pytest.fixture(scope='function')
    def vocabulary_read(self):
        class MockSession(object):
            @staticmethod
            def post(url, data, headers, files, allow_redirects, auth=None):
                datadict = json.loads(data.decode('utf-8'))
                return vocabulary_mockshow(url, datadict)

        Configuration.read().remoteckan().session = MockSession()

    @pytest.fixture(scope='function')
    def user_read(self):
        class MockSession(object):
            @staticmethod
            def post(url, data, headers, files, allow_redirects, auth=None):
                datadict = json.loads(data.decode('utf-8'))
                return user_mockshow(url, datadict)

        Configuration.read().remoteckan().session = MockSession()

    @pytest.fixture(scope='function')
    def organization_read(self):
        class MockSession(object):
            @staticmethod
            def post(url, data, headers, files, allow_redirects, auth=None):
                datadict = json.loads(data.decode('utf-8'))
                return organization_mockshow(url, datadict)

        Configuration.read().remoteckan().session = MockSession()

    @pytest.fixture(scope='function')
    def showcase_read(self):
        class MockSession(object):
            @staticmethod
            def post(url, data, headers, files, allow_redirects, auth=None):
                datadict = json.loads(data.decode('utf-8'))
                if 'showcase_list' in url:
                    result = json.dumps([showcase_resultdict])
                    return MockResponse(200,
                                        '{"success": true, "result": %s, "help": "http://test-data.humdata.org/api/3/action/help_show?name=ckanext_package_showcase_list"}' % result)
                if 'association_delete' in url:
                    TestDatasetNoncore.association = 'delete'
                    return MockResponse(200,
                                        '{"success": true, "result": null, "help": "http://test-data.humdata.org/api/3/action/help_show?name=ckanext_showcase_package_association_delete"}')
                elif 'association_create' in url:
                    TestDatasetNoncore.association = 'create'
                    result = json.dumps(datadict)
                    return MockResponse(200,
                                        '{"success": true, "result": %s, "help": "http://test-data.humdata.org/api/3/action/help_show?name=ckanext_showcase_package_association_create"}' % result)
                return dataset_mockshow(url, datadict)

        Configuration.read().remoteckan().session = MockSession()

    @pytest.fixture(scope='function')
    def vocabulary_update(self):
        class MockSession(object):
            @staticmethod
            def post(url, data, headers, files, allow_redirects, auth=None):
                if isinstance(data, dict):
                    datadict = {k.decode('utf8'): v.decode('utf8') for k, v in data.items()}
                else:
                    datadict = json.loads(data.decode('utf-8'))
                if 'default' in url:
                    result = json.dumps(resource_view_list)
                    return MockResponse(200,
                                        '{"success": true, "result": %s, "help": "http://test-data.humdata.org/api/3/action/help_show?name=package_create_default_resource_views"}' % result)
                if 'resource_view' in url:
                    if 'show' in url:
                        return resource_view_mockshow(url, datadict)
                    if 'list' in url:
                        return resource_view_mocklist(url, datadict)
                    if 'create' in url:
                        if datadict['title'] == 'Quick Charts':
                            return resource_view_mockcreate(url, datadict)
                    return MockResponse(404,
                                        '{"success": false, "error": {"message": "TEST ERROR: Not create", "__type": "TEST ERROR: Not Create Error"}, "help": "http://test-data.humdata.org/api/3/action/help_show?name=resource_view_create"}')

        Configuration.read().remoteckan().session = MockSession()

    def test_get_hdx_url(self, configuration, hdx_config_yaml, project_config_yaml):
        dataset = Dataset()
        assert dataset.get_hdx_url() is None
        datasetdata = copy.deepcopy(dataset_data)
        dataset = Dataset(datasetdata)
        assert dataset.get_hdx_url() == 'https://data.humdata.org/dataset/MyDataset1'
        Configuration.delete()
        Configuration._create(hdx_site='feature', user_agent='test', hdx_config_yaml=hdx_config_yaml,
                              project_config_yaml=project_config_yaml)
        dataset = Dataset(datasetdata)
        assert dataset.get_hdx_url() == 'https://feature.data-humdata-org.ahconu.org/dataset/MyDataset1'

    def test_get_set_dataset_date(self, configuration):
        datasetdata = copy.deepcopy(dataset_data)
        dataset = Dataset(datasetdata)
        assert dataset['dataset_date'] == '06/04/2016'
        assert dataset.get_dataset_date_as_datetime() == datetime.datetime(2016, 6, 4, 0, 0)
        assert dataset.get_dataset_date() == '2016-06-04'
        assert dataset.get_dataset_date('%Y/%m/%d') == '2016/06/04'
        testdate = datetime.datetime(2013, 12, 25, 0, 0)
        dataset.set_dataset_date_from_datetime(testdate)
        assert dataset['dataset_date'] == '12/25/2013'
        assert dataset.get_dataset_date_as_datetime() == testdate
        assert dataset.get_dataset_date() == '2013-12-25'
        assert dataset.get_dataset_date('%y-%m-%d %H:%M:%S%Z') == '13-12-25 00:00:00'
        dataset.set_dataset_date_from_datetime(testdate, testdate)
        assert dataset['dataset_date'] == '12/25/2013'
        dataset.set_dataset_date('2007-01-25T12:00:00Z')
        assert dataset['dataset_date'] == '01/25/2007'
        assert dataset.get_dataset_date_as_datetime() == datetime.datetime(2007, 1, 25, 0, 0)
        assert dataset.get_dataset_date() == '2007-01-25'
        assert dataset.get_dataset_date('%Y-%m-%dT%H:%M:%S%Z') == '2007-01-25T00:00:00'
        dataset.set_dataset_date('2013-09-11')
        assert dataset['dataset_date'] == '09/11/2013'
        assert dataset.get_dataset_date_as_datetime() == datetime.datetime(2013, 9, 11, 0, 0)
        assert dataset.get_dataset_date() == '2013-09-11'
        assert dataset.get_dataset_date('%Y/%m/%d') == '2013/09/11'
        test_date = '2021/05/06'
        dataset.set_dataset_date(test_date, date_format='%Y/%m/%d')
        assert dataset['dataset_date'] == '05/06/2021'
        assert dataset.get_dataset_date_as_datetime() == datetime.datetime(2021, 5, 6, 0, 0)
        assert dataset.get_dataset_date() == '2021-05-06'
        assert dataset.get_dataset_date('%Y/%m/%d') == test_date
        assert dataset.get_dataset_date_type() == 'date'
        test_date = '2021/05/06'
        dataset.set_dataset_date(test_date, None, '%Y/%m/%d', allow_range=False)
        assert dataset['dataset_date'] == '05/06/2021'
        test_end_date = '2021/07/08'
        dataset.set_dataset_date(test_date, test_end_date, '%Y/%m/%d')
        assert dataset['dataset_date'] == '05/06/2021-07/08/2021'
        assert dataset.get_dataset_date_as_datetime() == datetime.datetime(2021, 5, 6, 0, 0)
        assert dataset.get_dataset_end_date_as_datetime() == datetime.datetime(2021, 7, 8, 0, 0)
        assert dataset.get_dataset_date() == '2021-05-06'
        assert dataset.get_dataset_end_date() == '2021-07-08'
        assert dataset.get_dataset_date('%Y/%m/%d') == test_date
        assert dataset.get_dataset_end_date('%Y/%m/%d') == test_end_date
        assert dataset.get_dataset_date_type() == 'range'
        dataset.set_dataset_date(test_date, test_end_date, '%Y/%m/%d', allow_range=False)
        assert dataset['dataset_date'] == '05/06/2021-07/08/2021'
        dataset.set_dataset_date(test_date, test_end_date)
        assert dataset['dataset_date'] == '05/06/2021-07/08/2021'
        dataset.set_dataset_date(test_date, test_end_date, allow_range=False)
        assert dataset['dataset_date'] == '05/06/2021-07/08/2021'
        retval = dataset.set_dataset_year_range(2001, 2015)
        assert dataset.get_dataset_date_as_datetime() == datetime.datetime(2001, 1, 1, 0, 0)
        assert dataset.get_dataset_end_date_as_datetime() == datetime.datetime(2015, 12, 31, 0, 0)
        assert retval == [2001, 2015]
        retval = dataset.set_dataset_year_range('2010', '2017')
        assert dataset.get_dataset_date_as_datetime() == datetime.datetime(2010, 1, 1, 0, 0)
        assert dataset.get_dataset_end_date_as_datetime() == datetime.datetime(2017, 12, 31, 0, 0)
        assert retval == [2010, 2017]
        retval = dataset.set_dataset_year_range('2013')
        assert dataset.get_dataset_date_as_datetime() == datetime.datetime(2013, 1, 1, 0, 0)
        assert dataset.get_dataset_end_date_as_datetime() == datetime.datetime(2013, 12, 31, 0, 0)
        assert retval == [2013]
        retval = dataset.set_dataset_year_range({2005, 2002, 2003})
        assert dataset.get_dataset_date_as_datetime() == datetime.datetime(2002, 1, 1, 0, 0)
        assert dataset.get_dataset_end_date_as_datetime() == datetime.datetime(2005, 12, 31, 0, 0)
        assert retval == [2002, 2003, 2005]
        retval = dataset.set_dataset_year_range([2005, 2002, 2003])
        assert dataset.get_dataset_date_as_datetime() == datetime.datetime(2002, 1, 1, 0, 0)
        assert dataset.get_dataset_end_date_as_datetime() == datetime.datetime(2005, 12, 31, 0, 0)
        assert retval == [2002, 2003, 2005]
        retval = dataset.set_dataset_year_range((2005, 2002, 2003))
        assert dataset.get_dataset_date_as_datetime() == datetime.datetime(2002, 1, 1, 0, 0)
        assert dataset.get_dataset_end_date_as_datetime() == datetime.datetime(2005, 12, 31, 0, 0)
        assert retval == [2002, 2003, 2005]
        with pytest.raises(ParserError):
            dataset.set_dataset_date('lalala')
        with pytest.raises(ParserError):
            dataset.set_dataset_date('lalala', 'lalala')
        with pytest.raises(ParserError):
            dataset.set_dataset_date('lalala', 'lalala', date_format='%Y/%m/%d')
        with pytest.raises(HDXError):
            dataset.set_dataset_year_range(23.5)
        with pytest.raises(HDXError):
            dataset.set_dataset_year_range(2015, 23.5)
        del dataset['dataset_date']
        assert dataset.get_dataset_date_as_datetime() is None
        assert dataset.get_dataset_end_date_as_datetime() is None
        assert dataset.get_dataset_date() is None
        assert dataset.get_dataset_date('YYYY/MM/DD') is None
        assert dataset.get_dataset_date_type() is None
        dataset.set_dataset_date('2013-09')
        assert dataset['dataset_date'] == '09/01/2013-09/30/2013'
        dataset.set_dataset_date('2013-09', date_format='%Y-%m')
        assert dataset['dataset_date'] == '09/01/2013-09/30/2013'
        dataset.set_dataset_date('2013-09', dataset_end_date='2014-02')
        assert dataset['dataset_date'] == '09/01/2013-02/28/2014'
        dataset.set_dataset_date('2013-09', dataset_end_date='2014-02', date_format='%Y-%m')
        assert dataset['dataset_date'] == '09/01/2013-02/28/2014'
        dataset.set_dataset_date('2013')
        assert dataset['dataset_date'] == '01/01/2013-12/31/2013'
        dataset.set_dataset_date('2013', dataset_end_date='2014')
        assert dataset['dataset_date'] == '01/01/2013-12/31/2014'
        dataset.set_dataset_date('2013', dataset_end_date='2014', date_format='%Y')
        assert dataset['dataset_date'] == '01/01/2013-12/31/2014'
        with pytest.raises(ParserError):
            dataset.set_dataset_date('2013-09', allow_range=False)
        with pytest.raises(ParserError):
            dataset.set_dataset_date('2013-09', date_format='%Y-%m', allow_range=False)
        with pytest.raises(ParserError):
            dataset.set_dataset_date('2013-09', dataset_end_date='2014-02', allow_range=False)
        with pytest.raises(ParserError):
            dataset.set_dataset_date('2013-09', dataset_end_date='2014-02', date_format='%Y-%m', allow_range=False)

    def test_is_set_subnational(self):
        datasetdata = copy.deepcopy(dataset_data)
        dataset = Dataset(datasetdata)
        assert dataset['subnational'] == '1'
        assert dataset.is_subnational() is True
        dataset.set_subnational(False)
        assert dataset['subnational'] == '0'
        assert dataset.is_subnational() is False
        dataset.set_subnational(True)
        assert dataset['subnational'] == '1'
        assert dataset.is_subnational() is True

    def test_get_add_location(self, locations):
        Country.countriesdata(use_live=False)
        datasetdata = copy.deepcopy(dataset_data)
        dataset = Dataset(datasetdata)
        assert dataset['groups'] == resultgroups
        assert dataset.get_location() == ['Algeria', 'Zimbabwe']
        dataset.add_country_location('sdn')
        expected = copy.deepcopy(resultgroups)
        expected.append({'name': 'sdn'})
        assert dataset['groups'] == expected
        assert dataset.get_location() == ['Algeria', 'Zimbabwe', 'Sudan']
        dataset.add_country_location('dza')
        assert dataset['groups'] == expected
        assert dataset.get_location() == ['Algeria', 'Zimbabwe', 'Sudan']
        dataset.add_country_locations(['KEN', 'Mozambique', 'ken'])
        expected.extend([{'name': 'ken'}, {'name': 'moz'}])
        assert dataset['groups'] == expected
        assert dataset.get_location() == ['Algeria', 'Zimbabwe', 'Sudan', 'Kenya', 'Mozambique']
        dataset.remove_location('sdn')
        assert dataset.get_location() == ['Algeria', 'Zimbabwe', 'Kenya', 'Mozambique']
        with pytest.raises(HDXError):
            dataset.add_region_location('NOTEXIST')
        dataset.add_region_location('Africa')
        assert len(dataset['groups']) == 60
        assert len(dataset.get_location()) == 60
        del dataset['groups']
        assert dataset.get_location() == []
        with pytest.raises(HDXError):
            dataset.add_country_location('abc')
        with pytest.raises(HDXError):
            dataset.add_country_location('lala')
        dataset.add_country_location('Ukrai', exact=False)
        assert dataset['groups'] == [{'name': 'ukr'}]
        assert dataset.get_location() == ['Ukraine']
        dataset.add_country_location('ukr')
        dataset.add_other_location('nepal-earthquake')
        assert dataset['groups'] == [{'name': 'ukr'}, {'name': 'nepal-earthquake'}]
        assert dataset.get_location() == ['Ukraine', 'Nepal Earthquake']
        del dataset['groups']
        dataset.add_other_location('Nepal E', exact=False)
        assert dataset['groups'] == [{'name': 'nepal-earthquake'}]
        dataset.add_other_location('Nepal Earthquake')
        assert dataset['groups'] == [{'name': 'nepal-earthquake'}]
        with pytest.raises(HDXError):
            dataset.add_other_location('lala')
        with pytest.raises(HDXError):
            dataset.add_other_location('lala', alterror='nana')
        dataset['groups'] = [{'name': 'ken'}, {'name': 'MOZ'}, {'name': 'dza'}]
        dataset.remove_location('moz')
        assert dataset['groups'] == [{'name': 'ken'}, {'name': 'dza'}]
        dataset.remove_location('KEN')
        assert dataset['groups'] == [{'name': 'dza'}]

    def test_transform_update_frequency(self):
        assert len(Dataset.list_valid_update_frequencies()) == 32
        assert Dataset.transform_update_frequency('-2') == 'As needed'
        assert Dataset.transform_update_frequency('-1') == 'Never'
        assert Dataset.transform_update_frequency('0') == 'Live'
        assert Dataset.transform_update_frequency('1') == 'Every day'
        assert Dataset.transform_update_frequency('Adhoc') == '-2'
        assert Dataset.transform_update_frequency('As needed') == '-2'
        assert Dataset.transform_update_frequency('Never') == '-1'
        assert Dataset.transform_update_frequency('Live') == '0'
        assert Dataset.transform_update_frequency('Every day') == '1'
        assert Dataset.transform_update_frequency('EVERY WEEK') == '7'
        assert Dataset.transform_update_frequency('every month') == '30'
        assert Dataset.transform_update_frequency('LALA') is None
        assert Dataset.transform_update_frequency(-2) == 'As needed'
        assert Dataset.transform_update_frequency(7) == 'Every week'
        assert Dataset.transform_update_frequency('') is None
        assert Dataset.transform_update_frequency(23) is None
        assert Dataset.transform_update_frequency('15') is None
        assert Dataset.transform_update_frequency('Quarterly') == '90'

    def test_get_set_expected_update_frequency(self, configuration):
        datasetdata = copy.deepcopy(dataset_data)
        dataset = Dataset(datasetdata)
        assert dataset['data_update_frequency'] == '7'
        assert dataset.get_expected_update_frequency() == 'Every week'
        dataset.set_expected_update_frequency('every two weeks')
        assert dataset['data_update_frequency'] == '14'
        dataset.set_expected_update_frequency(30)
        assert dataset['data_update_frequency'] == '30'
        dataset.set_expected_update_frequency('Fortnightly')
        assert dataset['data_update_frequency'] == '14'
        assert dataset.get_expected_update_frequency() == 'Every two weeks'
        dataset.set_expected_update_frequency('EVERY SIX MONTHS')
        assert dataset['data_update_frequency'] == '180'
        assert dataset.get_expected_update_frequency() == 'Every six months'
        dataset.set_expected_update_frequency('90')
        assert dataset['data_update_frequency'] == '90'
        assert dataset.get_expected_update_frequency() == 'Every three months'
        with pytest.raises(HDXError):
            dataset.set_expected_update_frequency('lalala')
        with pytest.raises(HDXError):
            dataset.set_expected_update_frequency(9)
        del dataset['data_update_frequency']
        assert dataset.get_expected_update_frequency() is None

    def test_get_add_tags(self, configuration, vocabulary_read):
        datasetdata = copy.deepcopy(dataset_data)
        dataset = Dataset(datasetdata)
        assert dataset['tags'] == resulttags
        assert dataset.get_tags() == ['conflict', 'political violence']
        dataset.add_tag('LALA')
        assert dataset['tags'] == resulttags
        assert dataset.get_tags() == ['conflict', 'political violence']
        dataset.add_tag('conflict')
        expected = copy.deepcopy(resulttags)
        expected.append({'name': 'violence and conflict', 'vocabulary_id': '4381925f-0ae9-44a3-b30d-cae35598757b'})
        assert dataset['tags'] == expected
        assert dataset.get_tags() == ['conflict', 'political violence', 'violence and conflict']
        dataset.add_tags(['desempleo', 'desocupación', 'desempleo', 'conflict-related deaths'])
        assert dataset.get_tags() == ['conflict', 'political violence', 'violence and conflict', 'unemployment',
                                      'fatalities - deaths']
        dataset.remove_tag('violence and conflict')
        assert dataset.get_tags() == ['conflict', 'political violence', 'unemployment', 'fatalities - deaths']
        del dataset['tags']
        assert dataset.get_tags() == []
        dataset.add_tag('conflict-related deaths')
        assert dataset['tags'] == [
            {'name': 'violence and conflict', 'vocabulary_id': '4381925f-0ae9-44a3-b30d-cae35598757b'},
            {'name': 'fatalities - deaths', 'vocabulary_id': '4381925f-0ae9-44a3-b30d-cae35598757b'}]
        assert dataset.get_tags() == ['violence and conflict', 'fatalities - deaths']
        dataset.add_tag(u'conflict-related deaths')
        assert dataset.get_tags() == ['violence and conflict', 'fatalities - deaths']
        dataset.add_tag(u'cholera')
        assert dataset.get_tags() == ['violence and conflict', 'fatalities - deaths', 'cholera']
        dataset.remove_tag(u'violence and conflict')
        assert dataset.get_tags() == ['fatalities - deaths', 'cholera']
        dataset.add_tag('cholera')
        assert dataset.get_tags() == ['fatalities - deaths', 'cholera']

    def test_add_clean_tags(self, configuration, vocabulary_read):
        Vocabulary.set_tagsdict(None)
        Vocabulary.read_tags_mappings(failchained=False)
        datasetdata = copy.deepcopy(dataset_data)
        dataset = Dataset(datasetdata)
        assert dataset.get_tags() == ['conflict', 'political violence']
        assert dataset.clean_tags() == (['violence and conflict'], ['political violence'])
        dataset.add_tags(['nodeid123', 'transportation'])
        assert dataset.get_tags() == ['violence and conflict', 'transportation']
        dataset['tags'].append({'name': 'nodeid123', 'vocabulary_id': '4381925f-0ae9-44a3-b30d-cae35598757b'})
        assert dataset.clean_tags() == (['violence and conflict', 'transportation'], ['nodeid123'])
        assert dataset.get_tags() == ['violence and conflict', 'transportation']
        dataset.add_tags(['geodata', 'points'])
        assert dataset.clean_tags() == (['violence and conflict', 'transportation', 'geodata'], [])
        dataset.add_tag('financial')
        assert dataset.get_tags() == ['violence and conflict', 'transportation', 'geodata']
        dataset['tags'].append({'name': 'financial', 'vocabulary_id': '4381925f-0ae9-44a3-b30d-cae35598757b'})
        assert dataset.clean_tags() == (['violence and conflict', 'transportation', 'geodata'], ['financial'])
        dataset.add_tag('addresses')
        assert dataset.clean_tags() == (['violence and conflict', 'transportation', 'geodata', '3-word addresses'], [])
        dataset.remove_tag('3-word addresses')
        assert dataset.get_tags() == ['violence and conflict', 'transportation', 'geodata']
        dataset.add_tag('cultivos coca')
        assert dataset.clean_tags() == (['violence and conflict', 'transportation', 'geodata', 'food production'], [])
        dataset.remove_tag('food production')
        dataset.add_tag('atentados')
        assert dataset.get_tags() == ['violence and conflict', 'transportation', 'geodata', 'security incidents']
        dataset['tags'].append({'name': 'atentados', 'vocabulary_id': '4381925f-0ae9-44a3-b30d-cae35598757b'})
        assert dataset.clean_tags() == (['violence and conflict', 'transportation', 'geodata', 'security incidents'], [])
        dataset.remove_tag('security incidents')
        dataset.add_tag('windspeeds')
        assert dataset.clean_tags() == (['violence and conflict', 'transportation', 'geodata', 'wind speed'], [])
        dataset.add_tag('conservancies')
        assert dataset.get_tags() == ['violence and conflict', 'transportation', 'geodata', 'wind speed', 'protected areas']
        dataset.remove_tag('transportation')
        dataset.remove_tag('protected areas')
        assert dataset.get_tags() == ['violence and conflict', 'geodata', 'wind speed']

    def test_maintainer(self, configuration, user_read):
        dataset = Dataset(dataset_data)
        dataset.set_maintainer('9f3e9973-7dbe-4c65-8820-f48578e3ffea')
        maintainer = dataset.get_maintainer()
        assert maintainer['name'] == 'MyUser1'
        user = User(user_data)
        dataset.set_maintainer(user)
        maintainer = dataset.get_maintainer()
        assert maintainer['name'] == 'MyUser1'
        with pytest.raises(HDXError):
            dataset.set_maintainer('jpsmith')
        with pytest.raises(HDXError):
            dataset.set_maintainer(123)

    def test_organization(self, configuration, organization_read):
        dataset = Dataset(dataset_data)
        dataset.set_organization('b67e6c74-c185-4f43-b561-0e114a736f19')
        organization = dataset.get_organization()
        assert organization['name'] == 'acled'
        organization = Organization(organization_data)
        organization['name'] = 'TEST1'
        dataset.set_organization(organization)
        organization = dataset.get_organization()
        assert organization['name'] == 'acled'
        with pytest.raises(HDXError):
            dataset.set_organization('123')
        with pytest.raises(HDXError):
            dataset.set_organization(123)

    def test_add_update_delete_showcase(self, configuration, showcase_read):
        datasetdata = copy.deepcopy(dataset_data)
        dataset = Dataset(datasetdata)
        dataset['id'] = 'dataset123'
        showcases = dataset.get_showcases()
        assert len(showcases) == 1
        TestDatasetNoncore.association = None
        showcases[0]['id'] = '05e392bf-04e0-4ca6-848c-4e87bba10746'
        dataset.remove_showcase(showcases[0])
        assert TestDatasetNoncore.association == 'delete'
        TestDatasetNoncore.association = None
        assert dataset.add_showcase('15e392bf-04e0-4ca6-848c-4e87bba10745') is True
        assert TestDatasetNoncore.association == 'create'
        TestDatasetNoncore.association = None
        dataset.add_showcases([{'id': '15e392bf-04e0-4ca6-848c-4e87bba10745'}])
        assert TestDatasetNoncore.association == 'create'
        TestDatasetNoncore.association = None
        assert dataset.add_showcases([{'id': '15e392bf-04e0-4ca6-848c-4e87bba10745'}, {'id': '05e392bf-04e0-4ca6-848c-4e87bba10746'}]) is False
        assert TestDatasetNoncore.association == 'create'
        TestDatasetNoncore.association = None
        assert dataset.add_showcase({'name': 'TEST1'}) is True
        assert TestDatasetNoncore.association == 'create'
        TestDatasetNoncore.association = None
        with pytest.raises(HDXError):
            dataset.add_showcase('123')
        with pytest.raises(HDXError):
            dataset.add_showcase(123)

    def test_set_quickchart_resource(self, configuration):
        datasetdata = copy.deepcopy(dataset_data)
        resourcesdata = copy.deepcopy(resources_data)
        datasetdata['resources'] = resourcesdata
        dataset = Dataset(datasetdata)
        assert 'dataset_preview' not in dataset
        assert dataset.set_quickchart_resource('3d777226-96aa-4239-860a-703389d16d1f')['id'] == '3d777226-96aa-4239-860a-703389d16d1f'
        assert dataset['dataset_preview'] == 'resource_id'
        resources = dataset.get_resources()
        assert resources[0]['dataset_preview_enabled'] == 'False'
        assert resources[1]['dataset_preview_enabled'] == 'True'
        assert dataset.set_quickchart_resource(resources[0])['id'] == 'de6549d8-268b-4dfe-adaf-a4ae5c8510d5'
        assert resources[0]['dataset_preview_enabled'] == 'True'
        assert resources[1]['dataset_preview_enabled'] == 'False'
        assert dataset.set_quickchart_resource(resources[1].data)['id'] == '3d777226-96aa-4239-860a-703389d16d1f'
        assert resources[0]['dataset_preview_enabled'] == 'False'
        assert resources[1]['dataset_preview_enabled'] == 'True'
        assert dataset.set_quickchart_resource(0)['id'] == 'de6549d8-268b-4dfe-adaf-a4ae5c8510d5'
        assert resources[0]['dataset_preview_enabled'] == 'True'
        assert resources[1]['dataset_preview_enabled'] == 'False'
        assert dataset.set_quickchart_resource('12345') is None
        with pytest.raises(HDXError):
            dataset.set_quickchart_resource(True)
        dataset.preview_off()
        assert dataset['dataset_preview'] == 'no_preview'
        assert resources[0]['dataset_preview_enabled'] == 'False'
        assert resources[1]['dataset_preview_enabled'] == 'False'
        assert dataset.set_quickchart_resource('Resource2')['id'] == '3d777226-96aa-4239-860a-703389d16d1f'
        assert dataset['dataset_preview'] == 'resource_id'
        assert resources[0]['dataset_preview_enabled'] == 'False'
        assert resources[1]['dataset_preview_enabled'] == 'True'
        assert dataset.set_quickchart_resource({'name': 'Resource1'})['id'] == 'de6549d8-268b-4dfe-adaf-a4ae5c8510d5'
        assert dataset['dataset_preview'] == 'resource_id'
        assert resources[0]['dataset_preview_enabled'] == 'True'
        assert resources[1]['dataset_preview_enabled'] == 'False'

    def test_quickcharts_resource_last(self):
        datasetdata = copy.deepcopy(dataset_data)
        resourcesdata = copy.deepcopy(resources_data)
        datasetdata['resources'] = resourcesdata
        dataset = Dataset(datasetdata)
        assert dataset.quickcharts_resource_last() is False
        resource = {'name': 'QuickCharts-resource'}
        dataset.resources.insert(1, resource)
        assert dataset.quickcharts_resource_last() is True
        assert dataset.resources[2]['name'] == resource['name']
        assert dataset.quickcharts_resource_last() is True

    def test_generate_resource_view(self, configuration, vocabulary_update, static_resource_view_yaml):
        datasetdata = copy.deepcopy(dataset_data)
        resourcesdata = copy.deepcopy(resources_data)
        datasetdata['resources'] = resourcesdata
        dataset = Dataset(datasetdata)
        assert 'dataset_preview' not in dataset
        resourceview = dataset.generate_resource_view(path=static_resource_view_yaml)
        hxl_preview_config = json.loads(resourceview['hxl_preview_config'])
        assert resourceview['id'] == 'c06b5a0d-1d41-4a74-a196-41c251c76023'
        assert hxl_preview_config['bites'][0]['title'] == 'Sum of fatalities'
        assert hxl_preview_config['bites'][1]['title'] == 'Sum of fatalities grouped by admin1'
        assert hxl_preview_config['bites'][2]['title'] == 'Sum of fatalities grouped by admin2'
        resourceview = dataset.generate_resource_view(path=static_resource_view_yaml, bites_disabled=[False, True, False])
        hxl_preview_config = json.loads(resourceview['hxl_preview_config'])
        assert resourceview['id'] == 'c06b5a0d-1d41-4a74-a196-41c251c76023'
        assert hxl_preview_config['bites'][0]['title'] == 'Sum of fatalities'
        assert hxl_preview_config['bites'][1]['title'] == 'Sum of fatalities grouped by admin2'
        resourceview = dataset.generate_resource_view(path=static_resource_view_yaml, bites_disabled=[True, True, True])
        assert resourceview is None
        indicators = [{'code': '1', 'title': 'My1', 'unit': 'ones', 'description': 'This is my one!'},
                      {'code': '2', 'title': 'My2', 'unit': 'twos'},
                      {'code': '3', 'title': 'My3', 'description': 'This is my three!'}]
        resourceview = dataset.generate_resource_view(indicators=indicators)
        hxl_preview_config = json.loads(resourceview['hxl_preview_config'])
        assert resourceview['id'] == 'c06b5a0d-1d41-4a74-a196-41c251c76023'
        assert hxl_preview_config['bites'][0]['ingredient']['filters']['filterWith'][0]['#indicator+code'] == '1'
        assert hxl_preview_config['bites'][0]['ingredient']['description'] == 'This is my one!'
        assert hxl_preview_config['bites'][0]['uiProperties']['title'] == 'My1'
        assert hxl_preview_config['bites'][0]['computedProperties']['dataTitle'] == 'ones'
        assert hxl_preview_config['bites'][1]['ingredient']['filters']['filterWith'][0]['#indicator+code'] == '2'
        assert hxl_preview_config['bites'][1]['ingredient']['description'] == ''
        assert hxl_preview_config['bites'][1]['uiProperties']['title'] == 'My2'
        assert hxl_preview_config['bites'][1]['computedProperties']['dataTitle'] == 'twos'
        assert hxl_preview_config['bites'][2]['ingredient']['filters']['filterWith'][0]['#indicator+code'] == '3'
        assert hxl_preview_config['bites'][2]['ingredient']['description'] == 'This is my three!'
        assert hxl_preview_config['bites'][2]['uiProperties']['title'] == 'My3'
        assert hxl_preview_config['bites'][2]['computedProperties']['dataTitle'] == ''
        assert dataset.generate_resource_view(indicators=[]) is None
        assert dataset.generate_resource_view(indicators=[None, None, None]) is None
        assert dataset.generate_resource_view(resource='123', path=static_resource_view_yaml) is None
        del dataset.get_resources()[0]['id']
        resourceview = dataset.generate_resource_view(path=static_resource_view_yaml)
        assert 'id' not in resourceview
        assert 'resource_id' not in resourceview
        assert resourceview['resource_name'] == 'Resource1'
        with pytest.raises(IOError):
            dataset.generate_resource_view()

    def test_remove_dates_from_title(self):
        dataset = Dataset()
        with pytest.raises(HDXError):
            dataset.remove_dates_from_title()
        assert 'title' not in dataset
        title = 'Title with no dates'
        dataset['title'] = title
        assert dataset.remove_dates_from_title() == list()
        assert dataset['title'] == title
        assert 'dataset_date' not in dataset
        assert dataset.remove_dates_from_title(set_dataset_date=True) == list()
        title = 'ICA Armenia, 2017 - Drought Risk, 1981-2015'
        dataset['title'] = title
        expected = [(datetime.datetime(1981, 1, 1, 0, 0), datetime.datetime(2015, 12, 31, 0, 0)),
                    (datetime.datetime(2017, 1, 1, 0, 0), datetime.datetime(2017, 12, 31, 0, 0))]
        assert dataset.remove_dates_from_title(change_title=False) == expected
        assert dataset['title'] == title
        assert 'dataset_date' not in dataset
        assert dataset.remove_dates_from_title() == expected
        newtitle = 'ICA Armenia - Drought Risk'
        assert dataset['title'] == newtitle
        assert 'dataset_date' not in dataset
        dataset['title'] = title
        assert dataset.remove_dates_from_title(set_dataset_date=True) == expected
        assert dataset['title'] == newtitle
        assert dataset['dataset_date'] == '01/01/1981-12/31/2015'
        assert dataset.remove_dates_from_title() == list()
        dataset['title'] = 'Mon_State_Village_Tract_Boundaries 9999 2001'
        expected = [(datetime.datetime(2001, 1, 1, 0, 0), datetime.datetime(2001, 12, 31, 0, 0))]
        assert dataset.remove_dates_from_title(set_dataset_date=True) == expected
        assert dataset['title'] == 'Mon_State_Village_Tract_Boundaries 9999'
        assert dataset['dataset_date'] == '01/01/2001-12/31/2001'
        dataset['title'] = 'Mon_State_Village_Tract_Boundaries 2001 99'
        assert dataset.remove_dates_from_title(set_dataset_date=True) == expected
        assert dataset['title'] == 'Mon_State_Village_Tract_Boundaries 99'
        assert dataset['dataset_date'] == '01/01/2001-12/31/2001'
        dataset['title'] = 'Mon_State_Village_Tract_Boundaries 9999 2001 99'
        assert dataset.remove_dates_from_title(set_dataset_date=True) == expected
        assert dataset['title'] == 'Mon_State_Village_Tract_Boundaries 9999 99'
        assert dataset['dataset_date'] == '01/01/2001-12/31/2001'

    def test_generate_qc_resource_from_rows(self, configuration):
        with temp_dir('test') as folder:
            with Download(user_agent='test') as downloader:
                _, rows = downloader.get_tabular_rows(TestDatasetNoncore.url, dict_form=True, format='csv')
                rows = list(rows)
                dataset = Dataset({'name': 'test'})
                qc_filename = 'qc_conflict_data_alg.csv'
                resourcedata = {
                    'name': 'Conflict Data for Algeria',
                    'description': 'Conflict data with HXL tags'
                }
                columnname = 'EVENT_ID_CNTY'
                qc_indicator_codes = ['1416RTA', 'XXXXRTA', '2231RTA']
                resource = dataset.generate_qc_resource_from_rows(folder, qc_filename, rows, resourcedata, columnname,
                                                                  TestDatasetNoncore.hxltags, qc_indicator_codes)
                assert resource == {'name': 'Conflict Data for Algeria', 'description': 'Conflict data with HXL tags',
                                    'format': 'csv', 'resource_type': 'file.upload', 'url_type': 'upload'}
                assert_files_same(join('tests', 'fixtures', 'qc_from_rows', qc_filename), join(folder, qc_filename))
                qc_filename = 'qc_conflict_data_alg_one_col.csv'
                dataset.generate_qc_resource_from_rows(folder, qc_filename, rows, resourcedata, columnname,
                                                       TestDatasetNoncore.hxltags, qc_indicator_codes, headers=[columnname])
                assert_files_same(join('tests', 'fixtures', 'qc_from_rows', qc_filename), join(folder, qc_filename))
                rows = list()
                resource = dataset.generate_qc_resource_from_rows(folder, qc_filename, rows, resourcedata, columnname,
                                                                  TestDatasetNoncore.hxltags, qc_indicator_codes)
                assert resource is None

    def test_download_and_generate_resource(self, configuration):
        with temp_dir('test') as folder:
            filename = 'conflict_data_alg.csv'
            resourcedata = {
                'name': 'Conflict Data for Algeria',
                'description': 'Conflict data with HXL tags'
            }
            admin1s = set()

            def process_row(headers, row):
                row['lala'] = 'lala'
                admin1 = row.get('ADMIN1')
                if admin1 is not None:
                    admin1s.add(admin1)
                return row

            quickcharts = {'hashtag': '#event+code', 'values': ['1416RTA', 'XXXXRTA', '2231RTA'], 'numeric_hashtag': '#affected+killed', 'cutdown': 2}
            dataset = Dataset()
            with Download(user_agent='test') as downloader:
                success, results = dataset.download_and_generate_resource(
                    downloader, TestDatasetNoncore.url, TestDatasetNoncore.hxltags, folder, filename, resourcedata,
                    header_insertions=[(0, 'lala')], row_function=process_row, yearcol='YEAR', quickcharts=quickcharts)
                assert success is True
                assert results == {'startdate': datetime.datetime(2001, 1, 1, 0, 0), 'enddate': datetime.datetime(2002, 12, 31, 0, 0), 'bites_disabled': [False, True, False],
                                   'headers': ['lala', 'GWNO', 'EVENT_ID_CNTY', 'EVENT_ID_NO_CNTY', 'EVENT_DATE', 'YEAR', 'TIME_PRECISION', 'EVENT_TYPE', 'ACTOR1', 'ALLY_ACTOR_1', 'INTER1', 'ACTOR2', 'ALLY_ACTOR_2', 'INTER2', 'INTERACTION', 'COUNTRY', 'ADMIN1', 'ADMIN2', 'ADMIN3', 'LOCATION', 'LATITUDE', 'LONGITUDE', 'GEO_PRECISION', 'SOURCE', 'NOTES', 'FATALITIES'],
                                   'rows': [{'lala': '', 'GWNO': '', 'EVENT_ID_CNTY': '#event+code', 'EVENT_ID_NO_CNTY': '', 'EVENT_DATE': '#date+occurred', 'YEAR': '#date+year', 'TIME_PRECISION': '', 'EVENT_TYPE': '#event+type', 'ACTOR1': '#group+name+first', 'ALLY_ACTOR_1': '', 'INTER1': '', 'ACTOR2': '#group+name+second', 'ALLY_ACTOR_2': '', 'INTER2': '', 'INTERACTION': '', 'COUNTRY': '#country+name', 'ADMIN1': '#adm1+name', 'ADMIN2': '#adm2+name', 'ADMIN3': '#adm3+name', 'LOCATION': '#loc+name', 'LATITUDE': '#geo+lat', 'LONGITUDE': '#geo+lon', 'GEO_PRECISION': '', 'SOURCE': '#meta+source', 'NOTES': '#description', 'FATALITIES': '#affected+killed'},
                                            {'GWNO': '615', 'EVENT_ID_CNTY': '1416RTA', 'EVENT_ID_NO_CNTY': '', 'EVENT_DATE': '18/04/2001', 'YEAR': '2001', 'TIME_PRECISION': '1', 'EVENT_TYPE': 'Violence against civilians', 'ACTOR1': 'Police Forces of Algeria (1999-)', 'ALLY_ACTOR_1': '', 'INTER1': '1', 'ACTOR2': 'Civilians (Algeria)', 'ALLY_ACTOR_2': 'Berber Ethnic Group (Algeria)', 'INTER2': '7', 'INTERACTION': '17', 'COUNTRY': 'Algeria', 'ADMIN1': 'Tizi Ouzou', 'ADMIN2': 'Beni-Douala', 'ADMIN3': '', 'LOCATION': 'Beni Douala', 'LATITUDE': '36.61954', 'LONGITUDE': '4.08282', 'GEO_PRECISION': '1', 'SOURCE': 'Associated Press Online', 'NOTES': 'A Berber student was shot while in police custody at a police station in Beni Douala. He later died on Apr.21.', 'FATALITIES': '1', 'lala': 'lala'},
                                            {'GWNO': '615', 'EVENT_ID_CNTY': '2229RTA', 'EVENT_ID_NO_CNTY': '', 'EVENT_DATE': '19/04/2001', 'YEAR': '2001', 'TIME_PRECISION': '1', 'EVENT_TYPE': 'Riots/Protests', 'ACTOR1': 'Rioters (Algeria)', 'ALLY_ACTOR_1': 'Berber Ethnic Group (Algeria)', 'INTER1': '5', 'ACTOR2': 'Police Forces of Algeria (1999-)', 'ALLY_ACTOR_2': '', 'INTER2': '1', 'INTERACTION': '15', 'COUNTRY': 'Algeria', 'ADMIN1': 'Tizi Ouzou', 'ADMIN2': 'Tizi Ouzou', 'ADMIN3': '', 'LOCATION': 'Tizi Ouzou', 'LATITUDE': '36.71183', 'LONGITUDE': '4.04591', 'GEO_PRECISION': '3', 'SOURCE': 'Kabylie report', 'NOTES': 'Riots were reported in numerous villages in Kabylie, resulting in dozens wounded in clashes between protesters and police and significant material damage.', 'FATALITIES': '0', 'lala': 'lala'},
                                            {'GWNO': '615', 'EVENT_ID_CNTY': '2230RTA', 'EVENT_ID_NO_CNTY': '', 'EVENT_DATE': '20/04/2001', 'YEAR': '2002', 'TIME_PRECISION': '1', 'EVENT_TYPE': 'Riots/Protests', 'ACTOR1': 'Protesters (Algeria)', 'ALLY_ACTOR_1': 'Students (Algeria)', 'INTER1': '6', 'ACTOR2': '', 'ALLY_ACTOR_2': '', 'INTER2': '0', 'INTERACTION': '60', 'COUNTRY': 'Algeria', 'ADMIN1': 'Bejaia', 'ADMIN2': 'Amizour', 'ADMIN3': '', 'LOCATION': 'Amizour', 'LATITUDE': '36.64022', 'LONGITUDE': '4.90131', 'GEO_PRECISION': '1', 'SOURCE': 'Crisis Group', 'NOTES': 'Students protested in the Amizour area. At least 3 were later arrested for allegedly insulting gendarmes.', 'FATALITIES': '0', 'lala': 'lala'},
                                            {'GWNO': '615', 'EVENT_ID_CNTY': '2231RTA', 'EVENT_ID_NO_CNTY': '', 'EVENT_DATE': '21/04/2001', 'YEAR': '2001', 'TIME_PRECISION': '1', 'EVENT_TYPE': 'Riots/Protests', 'ACTOR1': 'Rioters (Algeria)', 'ALLY_ACTOR_1': 'Berber Ethnic Group (Algeria)', 'INTER1': '5', 'ACTOR2': 'Police Forces of Algeria (1999-)', 'ALLY_ACTOR_2': '', 'INTER2': '1', 'INTERACTION': '15', 'COUNTRY': 'Algeria', 'ADMIN1': 'Bejaia', 'ADMIN2': 'Amizour', 'ADMIN3': '', 'LOCATION': 'Amizour', 'LATITUDE': '36.64022', 'LONGITUDE': '4.90131', 'GEO_PRECISION': '1', 'SOURCE': 'Kabylie report', 'NOTES': 'Rioters threw molotov cocktails, rocks and burning tires at gendarmerie stations in Beni Douala, El-Kseur and Amizour.', 'FATALITIES': '0', 'lala': 'lala'}],
                                   'qcheaders': ['EVENT_ID_CNTY', 'EVENT_DATE', 'YEAR', 'EVENT_TYPE', 'ACTOR1', 'ACTOR2', 'COUNTRY', 'ADMIN1', 'ADMIN2', 'ADMIN3', 'LOCATION', 'LATITUDE', 'LONGITUDE', 'SOURCE', 'NOTES', 'FATALITIES'],
                                   'qcrows': [{'EVENT_ID_CNTY': '#event+code', 'EVENT_DATE': '#date+occurred', 'YEAR': '#date+year', 'EVENT_TYPE': '#event+type', 'ACTOR1': '#group+name+first', 'ACTOR2': '#group+name+second', 'COUNTRY': '#country+name', 'ADMIN1': '#adm1+name', 'ADMIN2': '#adm2+name', 'ADMIN3': '#adm3+name', 'LOCATION': '#loc+name', 'LATITUDE': '#geo+lat', 'LONGITUDE': '#geo+lon', 'SOURCE': '#meta+source', 'NOTES': '#description', 'FATALITIES': '#affected+killed'},
                                              {'EVENT_ID_CNTY': '1416RTA', 'EVENT_DATE': '18/04/2001', 'YEAR': '2001', 'EVENT_TYPE': 'Violence against civilians', 'ACTOR1': 'Police Forces of Algeria (1999-)', 'ACTOR2': 'Civilians (Algeria)', 'COUNTRY': 'Algeria', 'ADMIN1': 'Tizi Ouzou', 'ADMIN2': 'Beni-Douala', 'ADMIN3': '', 'LOCATION': 'Beni Douala', 'LATITUDE': '36.61954', 'LONGITUDE': '4.08282', 'SOURCE': 'Associated Press Online', 'NOTES': 'A Berber student was shot while in police custody at a police station in Beni Douala. He later died on Apr.21.', 'FATALITIES': '1'}, {'EVENT_ID_CNTY': '2231RTA', 'EVENT_DATE': '21/04/2001', 'YEAR': '2001', 'EVENT_TYPE': 'Riots/Protests', 'ACTOR1': 'Rioters (Algeria)', 'ACTOR2': 'Police Forces of Algeria (1999-)', 'COUNTRY': 'Algeria', 'ADMIN1': 'Bejaia', 'ADMIN2': 'Amizour', 'ADMIN3': '', 'LOCATION': 'Amizour', 'LATITUDE': '36.64022', 'LONGITUDE': '4.90131', 'SOURCE': 'Kabylie report', 'NOTES': 'Rioters threw molotov cocktails, rocks and burning tires at gendarmerie stations in Beni Douala, El-Kseur and Amizour.', 'FATALITIES': '0'}]}
                assert dataset['dataset_date'] == '01/01/2001-12/31/2002'
                assert admin1s == {'Bejaia', 'Tizi Ouzou'}
                resources = dataset.get_resources()
                assert resources == [{'name': 'Conflict Data for Algeria', 'description': 'Conflict data with HXL tags', 'format': 'csv', 'resource_type': 'file.upload', 'url_type': 'upload'},
                                     {'name': 'QuickCharts-Conflict Data for Algeria', 'description': 'Cut down data for QuickCharts', 'format': 'csv', 'resource_type': 'file.upload', 'url_type': 'upload'}]
                assert_files_same(join('tests', 'fixtures', 'gen_resource', filename), join(folder, filename))
                qc_filename = 'qc_%s' % filename
                assert_files_same(join('tests', 'fixtures', 'gen_resource', qc_filename), join(folder, qc_filename))

                def process_year(row):
                    year = row['YEAR']
                    if year == '2002':
                        return None
                    startdate, enddate = parse_date_range(year)
                    return {'startdate': startdate, 'enddate': enddate}

                quickcharts['cutdownhashtags'] = ['#event+code']
                del quickcharts['hashtag']
                success, results = dataset.download_and_generate_resource(
                    downloader, TestDatasetNoncore.url, TestDatasetNoncore.hxltags, folder, filename, resourcedata, header_insertions=[(0, 'lala')],
                    row_function=process_row, date_function=process_year, quickcharts=quickcharts)
                assert success is True
                assert results['startdate'] == datetime.datetime(2001, 1, 1, 0, 0)
                assert results['enddate'] == datetime.datetime(2001, 12, 31, 0, 0)
                assert dataset['dataset_date'] == '01/01/2001-12/31/2001'
                assert_files_same(join('tests', 'fixtures', 'gen_resource', 'min_%s' % qc_filename), join(folder, qc_filename))

                with pytest.raises(HDXError):
                    dataset.download_and_generate_resource(downloader, TestDatasetNoncore.url, TestDatasetNoncore.hxltags, folder, filename, resourcedata,
                                                           yearcol='YEAR', date_function=process_year)
                success, results = dataset.download_and_generate_resource(
                    downloader, TestDatasetNoncore.url, TestDatasetNoncore.hxltags, folder, filename, resourcedata, header_insertions=[(0, 'lala')],
                    row_function=process_row)
                assert success is True
                url = 'https://raw.githubusercontent.com/OCHA-DAP/hdx-python-api/master/tests/fixtures/empty.csv'
                success, results = dataset.download_and_generate_resource(
                    downloader, url, TestDatasetNoncore.hxltags, folder, filename, resourcedata, header_insertions=[(0, 'lala')],
                    row_function=process_row, yearcol='YEAR')
                assert success is False
                url = 'https://raw.githubusercontent.com/OCHA-DAP/hdx-python-api/master/tests/fixtures/gen_resource/test_data_no_data.csv'
                success, results = dataset.download_and_generate_resource(
                    downloader, url, TestDatasetNoncore.hxltags, folder, filename, resourcedata, header_insertions=[(0, 'lala')],
                    row_function=process_row, quickcharts=quickcharts)
                assert success is False
                url = 'https://raw.githubusercontent.com/OCHA-DAP/hdx-python-api/master/tests/fixtures/gen_resource/test_data_no_years.csv'
                success, results = dataset.download_and_generate_resource(downloader, url, TestDatasetNoncore.hxltags, folder, filename,
                                                                          resourcedata, header_insertions=[(0, 'lala')],
                                                                          row_function=process_row, yearcol='YEAR')
                assert success is False
