#### @Con7ext
### https://github.com/con7ext/instagramApi
import re
import os
import json
import datetime
import requests
from random import randint
from Agent import UserAgent
from datetime import datetime
from types import SimpleNamespace
class Request (requests.Session):
    def __init__(self, base_uri = None, *args, **kwargs):
        super(Request, self).__init__(*args, **kwargs)
        self.base_uri = base_uri
    def request(self, method, url, **kwargs):
        if 'http' in url:
            modified_url = url
        else:
            modified_url = self.base_uri + url
        return super(Request, self).request(method, modified_url, **kwargs)
class Instagram(object):

    def __init__(self, options = {
        'username': None,
        'password': None,
        'proxy': None
    }):
        self.options = SimpleNamespace(**options)
        self.baseUrl = 'https://www.instagram.com'
        self.credentials = {
            'username': self.options.username,
            'password': self.options.password
        }
        self.request = Request(self.baseUrl)
        if self.options.proxy is not None:
            self.request.proxies = {
                'http': f'http://{self.options.proxy}',
                'https': f'http://{self.options.proxy}'
            }
        self.request.headers = {
            'User-Agent': UserAgent().random,
            'Accept-Language': 'en-US',
            'X-Instagram-AJAX': '1',
            'X-CSRFToken': '',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': self.baseUrl
        }
        self.sharedData = None
    def jason(self, text):
        js = json.loads(text)
        return js

    def login(self, sharedData = False):
        req = self.request.get('/')
        if req.status_code != 200:
            return False, f'Unexpected status code: {req.status_code}'
        matches = re.findall(r'csrf_token":"(\w+)"', req.text)[0] or None
        self.request.headers['X-CSRFToken'] = matches
        encryptPassword = f'#PWD_INSTAGRAM_BROWSER:0:{datetime.now().timestamp()}:{self.credentials["password"]}'
        res = self.request.post('/accounts/login/ajax/', data={'username': self.credentials['username'], 'enc_password': encryptPassword})
        try:
            js = self.jason(res.text)
        except:
            return False, 'Sorry got unexpected response.'
        if res.status_code != 200:
            return False, js['message'] or 'Failed to login.'
        if not js['authenticated']:
            return False, 'Cannot authenticated you.'
        cookies = res.cookies.get_dict()
        self.request.headers = {
            'X-CSRFToken': cookies['csrftoken']
        }
        if sharedData:
            self.sharedData = self._sharedData()
        return True, 'Login Successfully.'
    
    def logout(self):
        return self.request.get('/accounts/logout/ajax/')
    
    def getMedia(self, media_uri):
        req = self.request.get(media_uri, params={'__a': '1'})
        js = self.jason(req.text)
        if not js['graphql']['shortcode_media']:
            return False
        return js['graphql']['shortcode_media']

    def _sharedData(self, uri = '/'):
        req = self.request.get(uri)
        if req.status_code != 200:
            return False, f'Unexpected status code: {req.status_code}'
        _sharedData = req.text.split('window._sharedData = ')[1]
        _end = _sharedData.split(';</script>')[0]
        return json.loads(_end)
    
    def userProfile(self, username):
        req = self.request.get(f'/{username}/?__a=1', headers={'Referer': self.baseUrl + f'/{username}/'})
        js = self.jason(req.text)
        if not js['graphql']['user']:
            return False
        return js['graphql']['user']
    
    def uploadPhoto(self, file):
        uploadId = datetime.now().timestamp()
        file = open(file, 'rb')
        fileContent = file.read()
        file.seek(0, os.SEEK_END)
        fileSizeBytes = file.tell()

        uploadHeaderParams = {
            'media_type': '1',
            'upload_id': str(uploadId),
            'upload_media_height': '1080',
            'upload_media_width': '1080',
            'xsharing_user_ids': json.dumps([]),
            'image_compression': json.dumps({
                'lib_name': 'moz',
                'lib_version': '3.1.m',
                'quality': '80'
            })
        }
        fileName = f'{uploadId}_0_{randint(1000000000, 9999999999)}'
        headerParams = {
            'x-entity-type': 'image/jpeg',
            'offset': '0',
            'x-entity-name': fileName,
            'x-instagram-rupload-params': json.dumps(uploadHeaderParams),
            'x-entity-length': str(fileSizeBytes),
            'Content-Length': str(fileSizeBytes),
            'Content-Type': 'application/octet-stream',
            'x-ig-app-id': '1217981644879628',
            'Accept-Encoding': 'gzip',
            'X-Pigeon-Rawclienttime': '{:.3f}'.format(datetime.now().timestamp() / 1000),
            'X-IG-Connection-Speed': f'{randint(1000, 3700)}kbps',
            'X-IG-Bandwidth-Speed-KBPS': '-1.000',
            'X-IG-Bandwidth-TotalBytes-B': '0',
            'X-IG-Bandwidth-TotalTime-MS': '0'
        }
        req = self.request.post(f'/rupload_igphoto/{fileName}', headers=headerParams, data=fileContent)
        js = self.jason(req.text)
        if "upload_id" not in req.text:
            return False, 'Upload File Failed'
        return True, js
    
    def posting(self, photo, caption = '', postType = 'feed'):
        isUploaded, returnedData = self.uploadPhoto(photo)
        if not isUploaded:
            return False, returnedData
        data = {
            'upload_id': returnedData['upload_id'],
            'caption': caption,
            'source_type': 'library',
            'usertags': '',
            'custom_accessibility_caption': ''
        }
        headers = {
            'Referer': 'https://www.instagram.com/create/details/',
        }
        req = self.request.post(f'/create/{"configure/" if postType == "feed" else "configure_to_story/"}', data=data, headers=headers)
        return req.text
    
    def search(self, query, context = 'blended'):
        return self.request.get('/web/search/topsearch/', params={'query': query, 'context': context}).text
    
    def like (self, media):
        mediaId = media
        if 'http' in media:
            mediaId = self.getMedia(media)['id']
        return self.request.post(f'/web/likes/{mediaId}/like/').text
    
    def comment(self, media, comment, reply_to_id = ''):
        mediaId = media
        if 'http' in media:
            mediaId = self.getMedia(media)['id']
        return self.request.post(f'/web/comments/{mediaId}/add/', data={'comment_text': comment, 'replied_to_comment_id': reply_to_id}).text
    
    def follow(self, username):
        userid = ''
        if username.isnumeric():
            userid = username
        else:
            userid = self.userProfile(username)['id']
        return self.request.post(f'/web/friendships/{userid}/follow/').text
    
    def report(self, username):
        userid = self.userProfile(username)
        if not userid:
            return False
        form = {
            'entry_point': '1',
            'location': '2',
            'object_type': '5',
            'object_id': userid['id'],
            'container_module': 'profilePage',
            'frx_prompt_request_type': '1'
        }
        req = self.request.post('/reports/web/get_frx_prompt/', data=form)
        if req.status_code != 200:
            return False
        www_form = self.jason(req.text)['response']['context']
        form2 = {
            'context': www_form,
            'selected_tag_type': 'ig_spam_v3' 
        }
        req2 = self.request.post('/reports/web/log_tag_selected/', data=form2)
        if req2.status_code != 200:
            return False
        form['frx_prompt_request_type'] = '2'
        form['selected_tag_types'] = '["ig_spam_v3"]'
        form['context'] = www_form
        res = self.request.post('/reports/web/get_frx_prompt/', data=form)
        if res.status_code != 200:
            return False
        return res.text
