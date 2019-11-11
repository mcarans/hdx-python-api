# -*- coding: UTF-8 -*-
"""Simple Facade Tests"""
from os.path import join

from hdx.utilities.useragent import UserAgentError, UserAgent

from hdx.facades import logging_kwargs
from hdx.version import get_api_version

logging_kwargs.update({
    'smtp_config_yaml': join('tests', 'fixtures', 'config', 'smtp_config.yml'),
})

import pytest

from . import testresult, my_testfnkw
from hdx.facades.keyword_arguments import facade


class TestKeywordArguments:
    def test_facade(self, monkeypatch, hdx_config_yaml, project_config_yaml):
        UserAgent.clear_global()
        my_user_agent = 'test'
        testresult.actual_result = None
        facade(my_testfnkw, user_agent=my_user_agent, hdx_config_yaml=hdx_config_yaml,
               project_config_yaml=project_config_yaml, fn='site')
        assert testresult.actual_result == 'https://data.humdata.org'
        UserAgent.clear_global()
        version = get_api_version()
        testresult.actual_result = None
        facade(my_testfnkw, user_agent=my_user_agent, hdx_config_yaml=hdx_config_yaml,
               project_config_yaml=project_config_yaml, fn='agent')
        assert testresult.actual_result == 'HDXPythonLibrary/%s-%s' % (version, my_user_agent)
        UserAgent.clear_global()
        testresult.actual_result = None
        my_user_agent = 'lala'
        monkeypatch.setenv('USER_AGENT', my_user_agent)
        facade(my_testfnkw, hdx_config_yaml=hdx_config_yaml, project_config_yaml=project_config_yaml, fn='agent')
        assert testresult.actual_result == 'HDXPythonLibrary/%s-%s' % (version, my_user_agent)
        UserAgent.clear_global()
        testresult.actual_result = None
        facade(my_testfnkw, user_agent='test', hdx_config_yaml=hdx_config_yaml, project_config_yaml=project_config_yaml,
               fn='agent')
        assert testresult.actual_result == 'HDXPythonLibrary/%s-%s' % (version, my_user_agent)
        UserAgent.clear_global()
        testresult.actual_result = None
        my_preprefix = 'haha'
        monkeypatch.setenv('PREPREFIX', my_preprefix)
        facade(my_testfnkw, user_agent='test', hdx_config_yaml=hdx_config_yaml, project_config_yaml=project_config_yaml,
               fn='agent')
        assert testresult.actual_result == '%s:HDXPythonLibrary/%s-%s' % (my_preprefix, version, my_user_agent)
        UserAgent.clear_global()
        testresult.actual_result = None
        my_test_key = '1234'
        facade(my_testfnkw, hdx_key=my_test_key, user_agent=my_user_agent, hdx_config_yaml=hdx_config_yaml,
               project_config_yaml=project_config_yaml, fn='api')
        assert testresult.actual_result == my_test_key
        UserAgent.clear_global()
        testresult.actual_result = None
        monkeypatch.setenv('HDX_KEY', my_test_key)
        facade(my_testfnkw, hdx_key='aaaa', user_agent=my_user_agent, hdx_config_yaml=hdx_config_yaml,
               project_config_yaml=project_config_yaml, fn='api')
        assert testresult.actual_result == my_test_key
        UserAgent.clear_global()
        testresult.actual_result = None
        my_test_hdxsite = 'test'
        facade(my_testfnkw, hdx_site=my_test_hdxsite, user_agent=my_user_agent, hdx_config_yaml=hdx_config_yaml,
               project_config_yaml=project_config_yaml, fn='site')
        assert testresult.actual_result == 'https://%s-data.humdata.org' % my_test_hdxsite
        UserAgent.clear_global()
        testresult.actual_result = None
        monkeypatch.setenv('HDX_SITE', my_test_hdxsite)
        facade(my_testfnkw, hdx_site='feature', user_agent=my_user_agent, hdx_config_yaml=hdx_config_yaml,
               project_config_yaml=project_config_yaml, fn='site')
        assert testresult.actual_result == 'https://%s-data.humdata.org' % my_test_hdxsite
        UserAgent.clear_global()
        my_test_hdxurl = 'http://other-data.humdata.org'
        monkeypatch.setenv('HDX_URL', my_test_hdxurl)
        facade(my_testfnkw, hdx_site='feature', user_agent=my_user_agent, hdx_config_yaml=hdx_config_yaml,
               project_config_yaml=project_config_yaml, fn='site')
        assert testresult.actual_result == my_test_hdxurl
        UserAgent.clear_global()
        my_test_hdxurl2 = 'http://other-data.humdata.org/'
        monkeypatch.setenv('HDX_URL', my_test_hdxurl2)
        facade(my_testfnkw, hdx_site='feature', user_agent=my_user_agent, hdx_config_yaml=hdx_config_yaml,
               project_config_yaml=project_config_yaml, fn='site')
        assert testresult.actual_result == my_test_hdxurl
        UserAgent.clear_global()

    def test_exception(self, hdx_config_yaml, project_config_yaml):
        UserAgent.clear_global()
        testresult.actual_result = None
        with pytest.raises(ValueError):
            facade(my_testfnkw, user_agent='test', hdx_config_yaml=hdx_config_yaml,
                   project_config_yaml=project_config_yaml, fn='exc')
        UserAgent.clear_global()
        with pytest.raises(UserAgentError):
            facade(my_testfnkw, hdx_config_yaml=hdx_config_yaml, project_config_yaml=project_config_yaml, fn='agent')
        UserAgent.clear_global()
