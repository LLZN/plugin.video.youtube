__author__ = 'bromix'

import time
import urlparse
import requests
from ...youtube.youtube_exceptions import LoginException
from ...kodion import Context
from __config__ import api, youtube_tv, keys_changed

context = Context()


class LoginClient(object):
    api_keys_changed = keys_changed

    CONFIGS = {
        'youtube-tv': {
            'system': 'YouTube TV',
            'key': youtube_tv['key'],
            'id': youtube_tv['id'],
            'secret': youtube_tv['secret']
        },
        'main': {
            'system': 'All',
            'key': api['key'],
            'id': api['id'],
            'secret': api['secret']
        }
    }

    def __init__(self, config=None, language='en-US', region='', access_token='', access_token_tv='', verify_ssl=False):
        self._config = self.CONFIGS['main'] if config is None else config
        self._config_tv = self.CONFIGS['youtube-tv']
        self._verify = verify_ssl
        # the default language is always en_US (like YouTube on the WEB)
        if not language:
            language = 'en_US'
            pass

        language = language.replace('-', '_')

        self._language = language
        self._region = region
        self._access_token = access_token
        self._access_token_tv = access_token_tv
        self._log_error_callback = None
        pass

    def set_log_error(self, callback):
        self._log_error_callback = callback
        pass

    def log_error(self, text):
        if self._log_error_callback:
            self._log_error_callback(text)
            pass
        else:
            print text
            pass
        pass

    def revoke(self, refresh_token):
        headers = {'Host': 'www.youtube.com',
                   'Connection': 'keep-alive',
                   'Origin': 'https://www.youtube.com',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.28 Safari/537.36',
                   'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                   'Accept': '*/*',
                   'DNT': '1',
                   'Referer': 'https://www.youtube.com/tv',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'en-US,en;q=0.8,de;q=0.6'}

        post_data = {'token': refresh_token}

        # url
        url = 'https://www.youtube.com/o/oauth2/revoke'

        result = requests.post(url, data=post_data, headers=headers, verify=self._verify)

        try:
            json_data = result.json()
            if 'error' in json_data:
                context.log_error('Revoke failed: JSON: |%s|' % json_data)
                raise LoginException(json_data['error'])
        except ValueError:
            json_data = None

        if result.status_code != requests.codes.ok:
            if json_data:
                response_dump = json_data
            else:
                try: response_dump = result.json()
                except ValueError:
                    try: response_dump = result.text
                    except: response_dump = 'None'
            context.log_error('Revoke failed: Response dump: |%s|' % response_dump)
            raise LoginException('Logout Failed')

        pass

    def refresh_token_tv(self, refresh_token, grant_type=''):
        client_id = str(self.CONFIGS['youtube-tv']['id'])
        client_secret = str(self.CONFIGS['youtube-tv']['secret'])
        return self.refresh_token(refresh_token, client_id=client_id,
                                  client_secret=client_secret, grant_type=grant_type)

    def refresh_token(self, refresh_token, client_id='', client_secret='', grant_type=''):
        headers = {'Host': 'www.youtube.com',
                   'Connection': 'keep-alive',
                   'Origin': 'https://www.youtube.com',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.28 Safari/537.36',
                   'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                   'Accept': '*/*',
                   'DNT': '1',
                   'Referer': 'https://www.youtube.com/tv',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'en-US,en;q=0.8,de;q=0.6'}

        client_id = client_id or self._config['id']
        client_secret = client_secret or self._config['secret']

        post_data = {'client_id': client_id,
                     'client_secret': client_secret,
                     'refresh_token': refresh_token,
                     'grant_type': 'refresh_token'}

        # url
        url = 'https://www.youtube.com/o/oauth2/token'

        config_type = self._get_config_type(client_id, client_secret)
        context.log_debug('Refresh token: Config: |%s| Client id [:5]: |%s| Client secret [:5]: |%s|' %
                          (config_type, client_id[:5], client_secret[:5]))

        result = requests.post(url, data=post_data, headers=headers, verify=self._verify)

        try:
            json_data = result.json()
            if 'error' in json_data:
                context.log_error('Refresh Failed: JSON: |%s|' % json_data)
                raise LoginException(json_data['error'])
        except ValueError:
            json_data = None

        if result.status_code != requests.codes.ok:
            if json_data:
                response_dump = json_data
            else:
                try: response_dump = result.json()
                except ValueError:
                    try: response_dump = result.text
                    except: response_dump = 'None'
            context.log_error('Refresh failed: Config: |%s| Client id [:5]: |%s| Client secret [:5]: |%s| Response dump |%s|' %
                              (config_type, client_id[:5], client_secret[:5], response_dump))
            raise LoginException('Login Failed')

        if result.headers.get('content-type', '').startswith('application/json'):
            if not json_data:
                json_data = result.json()
            access_token = json_data['access_token']
            expires_in = time.time() + int(json_data.get('expires_in', 3600))
            return access_token, expires_in

        return '', ''

    def get_device_token_tv(self, code, client_id='', client_secret='', grant_type=''):
        client_id = client_id or self.CONFIGS['youtube-tv']['id']
        client_secret = client_secret or self.CONFIGS['youtube-tv']['secret']
        return self.get_device_token(code, client_id=client_id, client_secret=client_secret, grant_type=grant_type)

    def get_device_token(self, code, client_id='', client_secret='', grant_type=''):
        headers = {'Host': 'www.youtube.com',
                   'Connection': 'keep-alive',
                   'Origin': 'https://www.youtube.com',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.28 Safari/537.36',
                   'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                   'Accept': '*/*',
                   'DNT': '1',
                   'Referer': 'https://www.youtube.com/tv',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'en-US,en;q=0.8,de;q=0.6',
                   'If-Match': '*'}

        client_id = client_id or self._config['id']
        client_secret = client_secret or self._config['secret']

        post_data = {'client_id': client_id,
                     'client_secret': client_secret,
                     'code': code,
                     'grant_type': 'http://oauth.net/grant_type/device/1.0'}

        # url
        url = 'https://www.youtube.com/o/oauth2/token'

        config_type = self._get_config_type(client_id, client_secret)
        context.log_debug('Retrieving device token: Config: |%s| Client id [:5]: |%s| Client secret [:5]: |%s|' %
                          (config_type, client_id[:5], client_secret[:5]))

        result = requests.post(url, data=post_data, headers=headers, verify=self._verify)

        try:
            json_data = result.json()
            if 'error' in json_data:
                if json_data['error'] != u'authorization_pending':
                    context.log_error('Retrieving device token: JSON: |%s|' % json_data)
                    raise LoginException(json_data['error'])
        except ValueError:
            json_data = None

        if result.status_code != requests.codes.ok:
            if json_data:
                response_dump = json_data
            else:
                try: response_dump = result.json()
                except ValueError:
                    try: response_dump = result.text
                    except: response_dump = 'None'
            context.log_error('Retrieving device token: Config: |%s| Client id [:5]: |%s| Client secret [:5]: |%s| Response dump |%s|' %
                              (config_type, client_id[:5], client_secret[:5], response_dump))
            raise LoginException('Login Failed: Code %s' % result.status_code)

        if result.headers.get('content-type', '').startswith('application/json'):
            if json_data: return json_data
            else: return result.json()

        return None

    def generate_user_code_tv(self):
        client_id = str(self.CONFIGS['youtube-tv']['id'])
        return self.generate_user_code(client_id=client_id)

    def generate_user_code(self, client_id=''):
        headers = {'Host': 'www.youtube.com',
                   'Connection': 'keep-alive',
                   'Origin': 'https://www.youtube.com',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.28 Safari/537.36',
                   'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                   'Accept': '*/*',
                   'DNT': '1',
                   'Referer': 'https://www.youtube.com/tv',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'en-US,en;q=0.8,de;q=0.6',
                   'If-Match': '*'}

        client_id = client_id or self._config['id']

        post_data = {'client_id': client_id,
                     'scope': 'https://www.googleapis.com/auth/youtube'}
        # 'scope': 'http://gdata.youtube.com https://www.googleapis.com/auth/youtube-paid-content'}

        # url
        url = 'https://www.youtube.com/o/oauth2/device/code'

        config_type = self._get_config_type(client_id)
        context.log_debug('Generating user code: Config: |%s| Client id [:5]: |%s|' %
                          (config_type, client_id[:5]))

        result = requests.post(url, data=post_data, headers=headers, verify=self._verify)

        try:
            json_data = result.json()
            if 'error' in json_data:
                context.log_error('Generate user code failed: JSON: |%s|' % json_data)
                raise LoginException(json_data['error'])
        except ValueError:
            json_data = None

        if result.status_code != requests.codes.ok:
            if json_data:
                response_dump = json_data
            else:
                try: response_dump = result.json()
                except ValueError:
                    try: response_dump = result.text
                    except: response_dump = 'None'
            context.log_error('Generate user code failed: Config: |%s| Client id [:5]: |%s| Response dump |%s|' %
                              (config_type, client_id[:5], response_dump))
            raise LoginException('Login Failed')

        if result.headers.get('content-type', '').startswith('application/json'):
            if json_data: return json_data
            else: return result.json()

        return None

    def get_access_token(self):
        return self._access_token

    def authenticate(self, username, password):
        headers = {'device': '38c6ee9a82b8b10a',
                   'app': 'com.google.android.youtube',
                   'User-Agent': 'GoogleAuth/1.4 (GT-I9100 KTU84Q)',
                   'content-type': 'application/x-www-form-urlencoded',
                   'Host': 'android.clients.google.com',
                   'Connection': 'Keep-Alive',
                   'Accept-Encoding': 'gzip'}

        post_data = {'device_country': self._region.lower(),
                     'operatorCountry': self._region.lower(),
                     'lang': self._language.replace('-', '_'),
                     'sdk_version': '19',
                     # 'google_play_services_version': '6188034',
                     'accountType': 'HOSTED_OR_GOOGLE',
                     'Email': username.encode('utf-8'),
                     'service': 'oauth2:https://www.googleapis.com/auth/youtube https://www.googleapis.com/auth/youtube.force-ssl https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/emeraldsea.mobileapps.doritos.cookie https://www.googleapis.com/auth/plus.stream.read https://www.googleapis.com/auth/plus.stream.write https://www.googleapis.com/auth/plus.pages.manage https://www.googleapis.com/auth/identity.plus.page.impersonation',
                     'source': 'android',
                     'androidId': '38c6ee9a82b8b10a',
                     'app': 'com.google.android.youtube',
                     # 'client_sig': '24bb24c05e47e0aefa68a58a766179d9b613a600',
                     'callerPkg': 'com.google.android.youtube',
                     # 'callerSig': '24bb24c05e47e0aefa68a58a766179d9b613a600',
                     'Passwd': password.encode('utf-8')}

        # url
        url = 'https://android.clients.google.com/auth'

        result = requests.post(url, data=post_data, headers=headers, verify=self._verify)
        if result.status_code != requests.codes.ok:
            raise LoginException('Login Failed')

        lines = result.text.replace('\n', '&')
        params = dict(urlparse.parse_qsl(lines))
        token = params.get('Auth', '')
        expires = int(params.get('Expiry', -1))
        if not token or expires == -1:
            raise LoginException('Failed to get token')

        return token, expires

    def _get_config_type(self, client_id, client_secret=None):
        """used for logging"""
        if client_secret is None:
            using_conf_tv = (client_id == self.CONFIGS['youtube-tv'].get('id'))
            using_conf_main = (client_id == self.CONFIGS['main'].get('id'))
        else:
            using_conf_tv = ((client_id == self.CONFIGS['youtube-tv'].get('id')) and (client_secret == self.CONFIGS['youtube-tv'].get('secret')))
            using_conf_main = ((client_id == self.CONFIGS['main'].get('id')) and (client_secret == self.CONFIGS['main'].get('secret')))
        if not using_conf_main and not using_conf_tv:
            return 'None'
        elif using_conf_tv:
            return 'YouTube TV'
        elif using_conf_main:
            return 'Add-on'
        else:
            return 'Unknown'
