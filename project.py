import statistics
from collections import Counter
import base64
import time
import random
from functools import partial
from flask import Flask, redirect, request, Response
import os
import spotipy
from spotipy import CacheFileHandler
from spotipy.oauth2 import SpotifyOAuth
from concurrent.futures import ThreadPoolExecutor
import config

ACOUSTICNESS = 'acousticness'
DANCEABILITY = 'danceability'
ENERGY = 'energy'
INSTRUMENTALNESS = 'instrumentalness'
LIVENESS = 'liveness'
SPEECHINESS = 'speechiness'
TEMPO = 'tempo'
VALENCE = 'valence'


class Auth:
    # Spotify API credentials
    CLIENTID = config.CLIENTID
    CLIENTSECRET = config.CLIENTSECRET
    REDIRECTURI = "http://localhost:3000/callback"

    # Create a CacheFileHandler instance with the desired cache_path
    CACHE_PATH = ".cache"
    cache_handler = CacheFileHandler(cache_path=CACHE_PATH)

    # Spotify OAuth configuration
    sp_oauth = SpotifyOAuth(CLIENTID, CLIENTSECRET, REDIRECTURI,
                            scope=["user-read-recently-played", "playlist-read-private", "playlist-read-collaborative",
                                   "playlist-modify-public", "playlist-modify-private", "ugc-image-upload",
                                   "user-read-email", "user-read-private"], cache_handler=cache_handler)

    def get_auth_url(self):
        # Get the authorization URL
        return self.sp_oauth.get_authorize_url()

    def get_spotify_session(self, code):
        # Get the access token, check if access token is expected type, then authorize with it and return active session
        access_token = self.sp_oauth.get_access_token(as_dict=False, code=code)
        type_of_access_token = type(access_token)

        if type_of_access_token != str:
            return f"Error access_token is not string, returned: {type_of_access_token}"

        return spotipy.Spotify(auth=access_token)


class SpotifyAPI:
    def __init__(self):
        # Initialize the SpotifyAPI object with a user session and an empty dictionary of target features.
        self.user_session = None
        self.target_features = {
            ACOUSTICNESS: [],
            DANCEABILITY: [],
            ENERGY: [],
            INSTRUMENTALNESS: [],
            LIVENESS: [],
            SPEECHINESS: [],
            TEMPO: [],
            VALENCE: [],
        }

    def __getitem__(self, key):
        # Retrieve the value associated with the given key from the target_features dictionary.
        return self.target_features[key]

    def __setitem__(self, key, value):
        # Set the value associated with the given key in the target_features dictionary.
        self.target_features[key] = value

    def get_playlists(self, limit):
        # Return current users playlist. The limit maximum is 50.
        return self.user_session.current_user_playlists(limit=limit)

    def get_tracks(self, limit, playlist_num=None, playlist_id=None):
        # Return the tracks based on user's choice of recently played/playlist tracks
        if playlist_num == 0:
            return self.get_recently_or_playlist(limit, True)
        else:
            return self.get_recently_or_playlist(limit, False, playlist_id)

    def get_recently_played_items(self, limit, after=None, before=None):
        # Return users recently played tracks
        return self.user_session.current_user_recently_played(limit=limit, after=after, before=before)

    def get_playlist_items(self, limit, fields=None, offset=0, market=None, playlist_id=None):
        # Return users playlist tracks with the playlist ID.
        return self.user_session.playlist_items(playlist_id=playlist_id, fields=fields, limit=limit, offset=offset,
                                                market=market)

    def get_recently_or_playlist(self, limit, recently_played, playlist_id=None):
        # Recently_played parameter can be True or False. Parameter defines if we grab the users recently played tracks
        # (True) or tracks from a playlist by playlist_id (False).
        # Return tracks from user depending on the given recently_played parameter
        tracks = []
        before = None
        offset = 0
        limit = int(limit)

        while limit > 0:
            # Since Spotify limits the number of songs that can be retrieved in a single request to 50, the code also
            # retrieves the songs in batches of 50.
            batch_limit = min(limit, 50)

            if recently_played:
                response = self.get_recently_played_items(limit=batch_limit, before=before)

                if before is not None:
                    before = response["cursors"]["before"]
                else:
                    break
            else:
                response = self.get_playlist_items(playlist_id=playlist_id, limit=batch_limit, offset=offset)

            tracks.extend(response['items'])
            limit -= batch_limit
            offset += batch_limit

            if len(response['items']) < batch_limit:
                # If there are no more tracks available, break out of while
                break

        return tracks

    def get_track_audio_features(self, track_ids):
        # Return audio features of tracks by track_ids in a dictionary.
        # A 'copy' of track_ids is created, because the already looped through elements need to be deleted from it.
        temporary_track_ids = list(track_ids)
        retrieve_num = len(temporary_track_ids)
        while retrieve_num > 0:
            # Since Spotify limits the number of songs that can be analyzed in a single request to 100, the code also
            # retrieve the songs audio features in batches of 100.
            batch_limit = min(retrieve_num, 100)
            tracks_audio_features = self.user_session.audio_features(tracks=temporary_track_ids[0:batch_limit])
            for track in tracks_audio_features:
                for key in self.target_features:
                    self.target_features[key].append(track[key])
            del temporary_track_ids[:batch_limit]
            retrieve_num -= batch_limit
            if retrieve_num == 0:
                # If there are no more tracks available, break out of while
                break

        # Overwrite the audio feature values in the target_features dictionary by key with the mean value of the values
        for key in self.target_features:
            self.target_features[key] = statistics.mean(self.target_features[key])

        return self.target_features

    def get_artist_info(self, artist_ids):
        # Return artist info by artist IDs.
        return self.user_session.artists(artist_ids)

    def get_recommended_tracks(self, seed_artists, limit=100):
        # Return track recommendations based on seed artist and the target audio features.
        # Seed_artists is a list of maximum 5 artist_ids
        return self.user_session.recommendations(seed_artists=seed_artists,
                                                 limit=limit,
                                                 target_acousticness=self.target_features.get(ACOUSTICNESS),
                                                 target_danceability=self.target_features.get(DANCEABILITY),
                                                 target_energy=self.target_features.get(ENERGY),
                                                 target_instrumentalness=self.target_features.get(INSTRUMENTALNESS),
                                                 target_liveness=self.target_features.get(LIVENESS),
                                                 target_speechiness=self.target_features.get(SPEECHINESS),
                                                 target_tempo=self.target_features.get(TEMPO),
                                                 target_valence=self.target_features.get(VALENCE))

    def create_playlist(self, name):
        # Creating a public playlist for the user and assign it to the user by user ID.
        return self.user_session.user_playlist_create(self.user_session.current_user()['id'],
                                                      name,
                                                      public=True,
                                                      collaborative=False,
                                                      description='A playlist, personalized for me.')

    def add_tracks_to_playlist(self, playlist_id, track_ids):
        # Add tracks to the newly created playlist.
        retrieve_num = len(track_ids)
        while retrieve_num > 0:
            # Since Spotify limits the number of songs that can be added in a single request to 100, the code also
            # adds the songs audio features in batches of 100.
            batch_limit = min(retrieve_num, 100)
            self.user_session.playlist_add_items(playlist_id, track_ids[0:99])
            del track_ids[:batch_limit]
            retrieve_num -= batch_limit
            if retrieve_num == 0:
                # If there are no more tracks available, break out of while
                break

    def add_cover_photo_to_playlist(self, playlist_id, imagebase64):
        # Add a cover image to the newly created playlist.
        try:
            self.user_session.playlist_upload_cover_image(playlist_id=playlist_id, image_b64=imagebase64)
            return True
        except spotipy.SpotifyException:
            return False


class SpotifyPlaylist:
    def __init__(self, sp_api):
        self.spotify_api = sp_api
        self.remaining_tracks = None

    @staticmethod
    def get_user_input(prompt, validation_func):
        # Return user input after validating using function given in validation_func param
        while True:
            user_input = input(prompt)
            if validation_func(user_input):
                return user_input

    @staticmethod
    def get_user_preferences(attribute, explanation):
        # Get user preference about audio features
        prompt = (f"\033[1m 10\033[0m - {explanation[10]}, \033[1m 0\033[0m - {explanation[0]}\n"
                  f"What is your preference in '{attribute}'? ")

        return SpotifyPlaylist.get_user_input(prompt=prompt, validation_func=SpotifyPlaylist.validate_audio_pref)

    @staticmethod
    def get_user_top_artists(tracks):
        # Get the top (max 10) artists based on a playlist or the recently played tracks.
        result = []
        for item in tracks:
            artists = item['track']['artists']
            for artist in artists:
                artist_id = artist['id']
                result.append(artist_id)

        artist_counts = Counter(result)
        return artist_counts.most_common(10)

    @staticmethod
    def print_top_artists(playlist_num, top_artists_names, top_artists, playlists_name=None):
        # Print out the top artists depending on user input given in playlist_num param
        if playlist_num == 0:
            print(f"\nBased on your recently played songs your top artists are:")
            for i in range(len(top_artists_names)):
                print(f"{top_artists_names[i]} - {top_artists[i][1]}")
        else:
            print(
                f"\nBased on your '{playlists_name}' playlist songs your top artists are:")
            for i in range(len(top_artists_names)):
                print(f"{top_artists_names[i]} - {top_artists[i][1]}")

    @staticmethod
    def recommended_tracks(seed_artists):
        # Retrieve the recommended tracks based on how many seed artist the user have.
        # Seed_artists is a list of maximum 5 artist_ids
        recommended_tracks = list()
        temporary_seed_artists = list(seed_artists)
        # A 'copy' of seed_artists is created, because the already looped through elements need to be deleted from it.
        retrieve_num = len(temporary_seed_artists)

        while retrieve_num > 0:
            # Since Spotify limits the number of songs that can be retrieved in a single request to 100, the code also
            # retrieves the songs in batches of 100.
            batch_limit = min(retrieve_num, 5)
            response = spotify_api.get_recommended_tracks(temporary_seed_artists[:batch_limit], limit=100)['tracks']
            recommended_tracks += response
            del temporary_seed_artists[:batch_limit]
            retrieve_num -= batch_limit

            if batch_limit == 0:
                # If there are no more tracks available, break out of while
                break

        return recommended_tracks

    def filter_recommendations(self, artist_included, artists_to_delete, recommendations, track_ids):
        # Return filtered recommendations based on user's choice
        if artist_included == 'Y':
            return self.filter_tracks(recommendations, track_ids)
        else:
            self.remaining_tracks = self.exclude_top_artists(artists_to_delete, recommendations)
            return self.filter_tracks(self.remaining_tracks, track_ids)

    @staticmethod
    def filter_tracks(tracks, filter_track_ids):
        # Return a filtered list of track ids that were not present in the filter_track_ids parameter
        track_ids = list()
        track_ids += [track["id"] for track in tracks]
        filtered_track_ids = [track_id for track_id in track_ids if track_id not in filter_track_ids]
        get_rid_of_duplicates = set(filtered_track_ids)
        filtered_track_ids = list(get_rid_of_duplicates)
        return filtered_track_ids

    @staticmethod
    def exclude_top_artists(artists_to_delete, tracks):
        # Return a filtered list of tracks which artist_id is not present in artists_to_delete parameter
        result = list()
        for track in tracks:
            has_top_artist = any(artist["id"] in artists_to_delete for artist in track["artists"])
            if not has_top_artist:
                result.append(track)
        return result

    @staticmethod
    def get_playlist_imagebase64():
        # Open a random cover photo as binary data, encode it to base64.
        list_of_cover_photos = ["1.jpeg", "2.jpeg"]
        random_cover_photo = random.choice(list_of_cover_photos)

        with open(random_cover_photo, 'rb') as imageFile:
            binary_data = imageFile.read()

            base64_encoded = base64.b64encode(binary_data)

        return base64_encoded

    @staticmethod
    def wait_for_playlist_cover_to_be_uploaded(playlist_id, base64encoded):
        # Set start time to measure elapsed time
        start_time = time.time()

        # Set max wait time to wait for image to be added to the created playlist
        timeout = 1000

        # Continue looping until the playlist image is successfully added or the timeout is reached.
        while True:
            # Attempt to add the playlist cover image using the provided base64-encoded data.
            success = spotify_api.add_cover_photo_to_playlist(playlist_id=playlist_id, imagebase64=base64encoded)

            # Check if the image was added successfully
            if success:
                print("Playlist cover image uploaded successfully")
                break

            # Check if the elapsed time has exceeded the specified timeout.
            elif time.time() - start_time > timeout:
                print("Timeout reached. Exiting loop.")
                break

            # If neither success nor timeout, continue waiting
            else:
                print("Waiting for playlist cover image to be uploaded...")

    @staticmethod
    def validate_playlist_index(input_str, num):
        # Validate the playlist index.
        if input_str.isdigit() and 0 <= int(input_str) <= num:
            return True
        else:
            print(f"Please enter a number between 0 and {num}.")
            return False

    @staticmethod
    def validate_track_limit(input_str):
        # Validate the track limit that gets retrieved.
        if input_str.isdigit() and 1 <= int(input_str) <= 500:
            return True
        else:
            print("Please enter a number between 1 and 500.")
            return False

    @staticmethod
    def validate_audio_pref(input_str):
        # Validate the audio features preferences.
        if input_str.isdigit() and 0 <= int(input_str) <= 10:
            return True
        else:
            print("Please enter a number between 0 and 10.")
            return False

    @staticmethod
    def validate_artist_inclusion(input_str):
        # Validate the top artist inclusion.
        if input_str == "Y":
            print(
                "Now, MelodyMystiqe based on your preference (0-10) and based on your top artists (included)"
                " will generate a playlist for you...\n")
            return True
        elif input_str == "N":
            print(
                "Now, MelodyMystiqe based on your preference (0-10) and based on your top artists (excluded)"
                " will generate a playlist for you...\n")
            return True
        else:
            return False

    @staticmethod
    def validate_playlist_name(input_str):
        # Validate the newly created playlist name.
        max_characters = 150
        if len(input_str) <= max_characters:
            return True
        else:
            print("Error: Playlist name exceeds the maximum character limit. Please try again.")
            return False

    @staticmethod
    def adjust_mean(user_preference, original_mean):
        # Calculate the adjusted mean value for each audio preference, based on the given user input.
        if original_mean > 10:
            adjusted_mean = original_mean + ((user_preference - 5) * 10)
        else:
            adjusted_mean = original_mean + ((user_preference - 5) / 10)
            adjusted_mean = max(adjusted_mean, 0)
            adjusted_mean = min(adjusted_mean, 1)
        return round(adjusted_mean, 1)


app = Flask(__name__)
app.secret_key = os.urandom(24)
auth = Auth()
spotify_api = SpotifyAPI()
spotify_playlist = SpotifyPlaylist(spotify_api)
executor = ThreadPoolExecutor(1)

print(
    "\n\nWelcome to MelodyMystique - your Spotify personalized playlist generator!\n"
    "After the Spotify authentication choose from your playlist list that you want\n"
    "MelodyMystique to use to base it's analysis from, or choose the\n"
    "'Use my recently played tracks' option If you like.\n"
    "To authenticate, please visit: http://localhost:3000\nAfter that, please go back to the CLI.\n\n")


def primary_func(response_code):
    spotify_api.user_session = auth.get_spotify_session(response_code)

    playlists = spotify_api.get_playlists(30)

    print("Your playlists:")
    print("0 - Use my recently played tracks")

    # Print out the current user playlists with an index, and how many tracks they contain.
    for index, playlist in enumerate(playlists['items']):
        print(f"{index + 1} - {playlist['name']} - {playlist['tracks']['total']} tracks")

    # Get a user input about the chosen playlist index, or the recently played tracks, then validate it, then set it.
    playlist_num = int(spotify_playlist.get_user_input(
        f"Type a playlist number 1 - {playlists['total']} that you think best reflects your style and "
        "want to analyze it, or type '0' to analyze your recently played songs. ",
        lambda input_str: spotify_playlist.validate_playlist_index(input_str, playlists['total'])))

    # Set all the playlist IDs for the current user.
    user_playlists_ids = [playlist["id"] for playlist in playlists["items"]]

    # Set the selected playlist ID.
    selected_playlist_id = user_playlists_ids[playlist_num - 1]

    # Get a user input about how many tracks they want to analyze (max 500), then validate it, then set it.
    track_limit = int(spotify_playlist.get_user_input("Type in how many tracks would you like to analyze (max 500): ",
                                                      lambda input_str: spotify_playlist.validate_track_limit(
                                                          input_str)))

    # Set the tracks.
    tracks = spotify_api.get_tracks(track_limit, playlist_num, selected_playlist_id)

    print("Retrieving your tracks, please wait...")

    print(f"Successfully retrieved {len(tracks)} tracks.")

    # Set the tracks' IDs from the tracks.
    track_ids = [track['track']['id'] for track in tracks]

    # Set the audio features for each track to a dictionary.
    features = spotify_api.get_track_audio_features(track_ids)

    # Explanations for the audio features.
    audio_explanations = {
        ACOUSTICNESS: {
            10: "acoustic instruments like guitars, pianos, or live vocals",
            0: "more electronic or synthesized sound"
        },
        DANCEABILITY: {
            10: "strong and steady rhythm, consistent tempo, and other musical elements that make it easy to move to",
            0: "more irregular rhythm, slower tempo, or other characteristics that make it less suitable for dancing"
        },
        ENERGY: {
            10: "more dynamic, loud, and intense. It often has a strong and powerful sound",
            0: "more subdued and relaxed feel, with less intensity and a more calming vibe"
        },
        INSTRUMENTALNESS: {
            10: "more likely to be instrumental, meaning it doesnt have vocals or has minimal vocal content",
            0: "more likely to have vocals"
        },
        LIVENESS: {
            10: "more likely to have been recorded during a live performance, capturing the energy and"
                " ambiance of a live show",
            0: "more likely to be a studio recording"
        },
        SPEECHINESS: {
            10: "more likely to contain spoken words or be a spoken-word piece, such as rap",
            0: "more likely to be instrumental or have minimal spoken-word content"
        },
        TEMPO: {
            10: "faster-paced track with a quicker rhythm",
            0: "slower-paced track with a more relaxed rhythm"
        },
        VALENCE: {
            10: "more likely to have a positive, happy, or cheerful mood",
            0: "more likely to have a negative, sad, or somber mood"
        }
    }

    # Replace all the audio features with the adjusted audio features.
    for key, values in audio_explanations.items():
        features[key] = spotify_playlist.adjust_mean(
            int(spotify_playlist.get_user_preferences(key, values)), features[key])

    # Set the top artist IDs.
    top_artist_ids = [artistID[0] for artistID in spotify_playlist.get_user_top_artists(tracks)]

    # Set the top artist names.
    top_artists_names = [name["name"] for name in spotify_api.get_artist_info(top_artist_ids)["artists"]]

    # Print out the top artists for the user
    spotify_playlist.print_top_artists(playlist_num, top_artists_names,
                                       spotify_playlist.get_user_top_artists(tracks),
                                       playlists['items'][playlist_num - 1]['name'])

    # Get a user input about the top artist inclusion, then validate it, then set it.
    artist_inclusion = spotify_playlist.get_user_input(
        "Type 'Y' if you want to include these artists in your personalized playlist.\n"
        "Type 'N' if you choose to exclude these artists.\n"
        "If you type 'N', your resulting personalized playlist will contain fewer tracks, "
        "but its most likely that you will get tracks from artists that you never heard before. ",
        spotify_playlist.validate_artist_inclusion)

    # Set the recommended tracks.
    recommendations = spotify_playlist.recommended_tracks(top_artist_ids)

    # Set the filtered tracks IDs.
    final_track_ids = spotify_playlist.filter_recommendations(artist_inclusion, top_artist_ids, recommendations,
                                                              track_ids)

    # Get a user input about the playlist name, then validate it, then set it.
    playlist_name = spotify_playlist.get_user_input(
        "Type in (max 150 characters) what the name of your personalized playlist should be: ",
        spotify_playlist.validate_playlist_name)

    # Set the created playlist.
    melody_mystique_playlist = spotify_api.create_playlist(playlist_name)

    # Set the created playlist ID.
    generated_playlist_id = melody_mystique_playlist['id']

    # Add tracks to the created playlist.
    spotify_api.add_tracks_to_playlist(generated_playlist_id, final_track_ids)

    # Set the cover image base64.
    img_base64 = spotify_playlist.get_playlist_imagebase64()
    spotify_playlist.wait_for_playlist_cover_to_be_uploaded(generated_playlist_id, img_base64)

    print("Check your Spotify playlists. MelodyMystique generated a personalized playlist for you!")


@app.route('/')
def login():
    # Initiate the Spotify authentication
    return redirect(auth.get_auth_url())


@app.route('/callback')
def callback():
    # Run the primary_func in a separate thread and let the current function return its response
    executor.submit(partial(primary_func, request.args["code"]))
    return Response("You can close this window, please go back to the CLI.", mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="localhost", port=3000)
