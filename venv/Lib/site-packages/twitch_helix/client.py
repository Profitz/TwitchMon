import json
import os.path
from typing import List

import requests

from .exceptions import *
from .models import *


class HelixClient:
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: List[str]
    access_token: str
    refresh_token: str
    app_token: str
    tokenfilename: str

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, scope: List[str], tokenfilename: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.tokenfilename = tokenfilename
        self.access_token = ''
        self.refresh_token = ''
        self.app_token = ''
        if os.path.exists(self.tokenfilename):
            with open(self.tokenfilename) as tokenfile:
                token = json.load(tokenfile)
                if set(token['scope']) == set(self.scope):
                    self.access_token = token['access_token']
                    self.refresh_token = token['refresh_token']
                    self.scope = token['scope']
                    self.app_token = token['app_token']
                else:
                    self.get_code_input()
                    self.get_app_token()
        else:
            self.get_code_input()
            self.get_app_token()

    def save_token(self):
        with open(self.tokenfilename, 'w') as tokenfile:
            json.dump({
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'scope': self.scope,
                'app_token': self.app_token,
            }, tokenfile)

    def get_code_url(self):
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.scope),
            'state': 'mystate',
        }
        query = '&'.join(f'{key}={item}' for key, item in params.items())
        url = 'https://id.twitch.tv/oauth2/authorize'
        if query:
            url = f'{url}?{query}'
        return url

    def get_code_input(self):
        url = self.get_code_url()
        print(f'Go to {url}')
        code = input('Enter the code from the redirect url')
        self.get_token(code)

    def get_token(self, code: str):
        r = requests.post('https://id.twitch.tv/oauth2/token', params={
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,
        })
        data = r.json()
        self.access_token = data['access_token']
        self.refresh_token = data['refresh_token']
        self.scope = data['scope']
        self.save_token()

    def refresh(self):
        r = requests.post('https://id.twitch.tv/oauth2/token', params={
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        })
        data = r.json()
        self.access_token = data['access_token']
        self.refresh_token = data['refresh_token']
        self.scope = data['scope']
        self.save_token()

    def get_app_token(self):
        r = requests.post('https://id.twitch.tv/oauth2/token', params={
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
            'scope': ' '.join(self.scope),
        })
        self.app_token = r.json()['access_token']
        self.save_token()

    def _request(self, method: str, endpoint: str, params: dict, json: dict, use_app_token: bool):
        headers = {
            'Authorization': f'Bearer {self.app_token if use_app_token else self.access_token}',
            'Client-Id': self.client_id,
        }
        r = requests.request(method, f'https://api.twitch.tv/helix/{endpoint}', params=params, json=json,
                             headers=headers)
        if r.status_code == 200:
            return r.json()['data']
        if r.status_code == 202:
            return r.json()['data']
        if r.status_code == 204:
            return None
        if r.status_code == 400:
            raise HelixMissingParameter()
        if r.status_code == 401:
            reason = r.json()['message']
            if reason == 'Invalid OAuth token':
                raise HelixExpiredToken()
            else:
                raise HelixError()
        if r.status_code == 500:
            raise HelixInternalServerError()
        raise HelixError()

    def request(self, method: str, endpoint: str, params: dict = None, json: dict = None, use_app_token: bool = False):
        try:
            return self._request(method, endpoint, params, json, use_app_token)
        except HelixExpiredToken:
            self.refresh()
            return self._request(method, endpoint, params, json, use_app_token)

    def get_user(self, id: str = None, login_name: str = None):
        params = {}
        if id:
            params['id'] = id
        if login_name:
            params['login'] = login_name
        return self.request('get', 'users', params)[0]

    def get_channel_info(self, broadcaster_id: str) -> ChannelInfo:
        r = self.request('get', 'channels', params={'broadcaster_id': broadcaster_id})
        return ChannelInfo.from_json(r[0])

    def modify_channel_info(self, broadcaster_id: str, channel_info: ChannelInfo):
        self.request('patch', 'channels', params={'broadcaster_id': broadcaster_id},
                     json=channel_info.to_json())

    def _update_reward_redemption(self, id: str, broadcaster_id: str, reward_id: str, status: str) -> RewardRedemption:
        r = self.request(
            'patch',
            'channel_points/custom_rewards/redemptions',
            params={
                'id': id,
                'broadcaster_id': broadcaster_id,
                'reward_id': reward_id,
            },
            json={
                'status': status
            }
        )
        return RewardRedemption.from_json(r[0])

    def fulfill_reward_redemption(self, id: str, broadcaster_id: str, reward_id: str) -> RewardRedemption:
        return self._update_reward_redemption(id, broadcaster_id, reward_id, 'FULFILLED')

    def cancel_reward_redemption(self, id: str, broadcaster_id: str, reward_id: str) -> RewardRedemption:
        return self._update_reward_redemption(id, broadcaster_id, reward_id, 'CANCELED')

    def eventsub_subscribe(self, type: str, version: str, condition: Condition, transport: Transport):
        return self.request('post', 'eventsub/subscriptions', json={
            'type': type,
            'version': version,
            'condition': condition.to_json(),
            'transport': transport.to_json(),
        }, use_app_token=True)

    def eventsub_delete(self, id: str):
        return self.request('delete', 'eventsub/subscriptions', params={'id': id}, use_app_token=True)

    def eventsub_list(self):
        # TODO add filter options
        return self.request('get', 'eventsub/subscriptions', use_app_token=True)
