# OAuth based off: https://www.youtube.com/watch?v=olY_2MW4Eik

import os
from dotenv import load_dotenv

import requests
import urllib.parse

from datetime import datetime, timedelta
from flask import Flask, redirect, request, jsonify, session, render_template

# Load environment variables from .env file
load_dotenv()

# Setup Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET')

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

AUTH_URL = os.getenv('AUTH_URL')
TOKEN_URL = os.getenv('TOKEN_URL')
API_BASE_URL = os.getenv('API_BASE_URL')

@app.route('/')
def index():
    """
    Index page that serves as a dashboard.
    """
    access_redirect = checkAccess(session)
    if access_redirect:
        return access_redirect

    loggedInUser = getUser()
    
    topArtists = getTopItems('artists', 3)
    topArtistsFiltered = []
    for item in topArtists:
        topArtistsFiltered.append({
            "img": item['images'][2]['url'],
            "name": item['name']
        })

    topTracks = getTopItems('tracks', 3)
    topTracksFiltered = []
    for item in topTracks:
        topTracksFiltered.append({
            "img": item['album']['images'][2]['url'],
            "name": item['name']
        })
    
    playlistsFiltered = []
    playlists = getPlaylists(3)['items']
    for item in playlists:
        playlistsFiltered.append({
            "img": item['images'][0]['url'],
            "name": item['name']
        })

    return render_template('index.html',
        topArtists = topArtistsFiltered,
        topTracks = topTracksFiltered,
        playlists = playlistsFiltered,
        user = loggedInUser
    )


@app.route('/login')
def login():
    """
    Login redirecting to Spotify authorization.
    """
    scope = 'user-read-private user-read-email user-top-read'

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True # false on default, just for testing here
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)


@app.route('/callback')
def callback():
    """
    Callback triggered by Spotify after attempting login.
    Currently redirecting to /playlists.
    """
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})
    
    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        return redirect('/')


@app.route('/playlists')
def get_playlists():
    """
    Shows the playlist of the authorized user.
    """
    access_redirect = checkAccess(session)
    if access_redirect:
        return access_redirect
    
    playlists = getPlaylists()

    return jsonify(playlists)


@app.route('/tracks')
def get_tracks():
    """
    Shows the top tracks of the authorized user.
    """
    access_redirect = checkAccess(session)
    if access_redirect:
        return access_redirect
    
    topTracks = getTopItems('tracks')

    return jsonify(topTracks)


@app.route('/artists')
def get_artists():
    """
    Shows the top tracks of the authorized user.
    """
    access_redirect = checkAccess(session)
    if access_redirect:
        return access_redirect
    
    topArtists = getTopItems('artists')

    return jsonify(topArtists)


@app.route('/refresh-token')
def refresh_token():
    """
    Refreshes the token given by Spotify if necessary.
    """
    access_redirect = checkAccess(session, True, False)
    if access_redirect:
        return access_redirect
    
    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        return redirect('/')


def checkAccess(session, checkLogin = True, checkTimestamp = True):
    """
    Checks the access of this session, redirects to login or referesh if required.
    """
    if checkLogin:
        if 'access_token' not in session:
            return redirect('/login')
    
    if checkTimestamp:
        if datetime.now().timestamp() > session['expires_at']:
            return redirect('/refresh-token')
        
    return None


def getUser():    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + 'me', headers=headers)
    user = response.json()

    return user


def getPlaylists(limit = 20):
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + f"me/playlists?limit={limit}", headers=headers)
    playlists = response.json()

    return playlists


def getTopItems(itemType, limit = 20):
    if itemType not in ['tracks', 'artists']:
        print("type does not fit")
        return redirect('/')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + f"me/top/{itemType}?limit={limit}", headers=headers)
    topItems = response.json()['items']

    return topItems


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)