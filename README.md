# MelodyMystique - Spotify Personalized Playlist Generator

<img src="./1.jpeg" width="200"> <img src="./2.jpeg" width="200">


This is my final project for Harvard's CS50P.

Are you bored with Spotify's 'Discover Weekly' music choices? Do you feel that the numbers of recommended songs are
not enough?

MelodyMystique is written in Python and designed to be used via the command line. It creates a personalized playlist
for you in Spotify, based on your recently played tracks or one of your playlists. It uses the chosen
playlist or recently played tracks most common (max 10) artists, and the track's audio features adjusted with your
preferred value to create a personalized playlist.

## Video Demo:
https://youtu.be/YZNtYBTCVSI


## Description:
You can choose how many tracks of your playlist (or recently played tracks) you'd like to have analyzed. Each of
these track's audio features _(acousticness, danceability, energy, instrumentalness, liveness, speechiness, tempo,
valence)_ gets analyzed. A mean value will be calculated for each of them.

You will be asked to position these preferences on a 0–10 scale. Based on these preferences, the mean value
will be adjusted.

It will print out information about the top artists. You have to choose if you want to include tracks from these
artists or not in the personalized playlist.

Finally, nothing else to do but name the newly created playlist, and enjoy the music! :musical_note:

How it works? [Jump to how it works.](#how-it-works)

## Getting Started

### Dependencies:

* ***Libraries***:
  * [**Spotipy**](https://spotipy.readthedocs.io/en/2.22.1/): Spotipy is a Python library for the Spotify Web API. With
  Spotipy you get full access to all the music data provided by the Spotify platform.
  * [**Flask**](https://flask.palletsprojects.com/en/3.0.x/): Flask is a Python web framework that provides useful tools
  and features that make creating web applications in Python easier.


You can install these libraries with:
    ```
    pip install -r requirements.txt
    ```

* ***Prerequisites***:
  * Spotify account
  * Spotify API credentials (client ID and client secret) [How to set up Spotify API credentials.](#set-up-your-spotify-api-credentials)
  * Python 3.x installed

### Executing program
1. Open a terminal window.

2. Navigate to the project directory:

    ```bash
    cd path/to/project
    ```
3. Run the following command:

    ```bash
    python project.py
   ```
4. You will get a welcome message:
    ```
   "Welcome to MelodyMystique - your Spotify personalized playlist generator!
   After the Spotify authentication choose from your playlist list that you want MelodyMystique to use
   to base it's analysis from, or choose the 'Use my recently played tracks' option If you like.

    To authenticate, please visit: http://localhost:3000
    After that, please go back to the CLI."
    ```

5. Use `Ctrl` + `Left click` to open the http://localhost:3000 link from the CLI.

6. Log in:
   * If you are not already logged in into Spotify, in the new tab that opened, you have to log in to your Spotify
   account; then the following message will appear below.
   * If you are already loggen in into Spotify, a white tab will open with the following message:
    ```
   "You can close this window, please go back to the CLI."
   ```

7. Go back to the CLI. You will see some information about your Spotify playlists. All of them are listed with an associated index number, and the amount of tracks they contain. Choose a playlist that you think best reflects your taste in music, or choose
your recently played tracks. If you chose, type in its index, and hit `Enter`.
8. Now, you have to type in how many tracks from the playlist or recently played tracks you want analyzed. The max
number is 500. Hit `Enter`.
9. You will get information about the amount of tracks that have been retrieved from the playlist or the recently played tracks.
10. MelodyMystique will analyze each of the tracks and get a mean value for each of the audio features.
_(acousticness, danceability, energy, instrumentalness, liveness, speechiness, tempo, valence)_
11. You will be asked 8 questions with explanations about your preference in each audio feature. You will
position them on a scale from 0 to 10. The mean value for each of the audio features will be adjusted based on
the number that you gave. Hit `Enter` after each of them.

   #### Example:

   You chose a playlist with 85 tracks. You chose to analyze 70 tracks from it. MelodyMystiqe will get
   each of the track's audio features, and then one-by-one calculate a mean value for each of the audio features.

   " **10** - acoustic instruments like guitars, pianos, or live vocals, **0** - more electronic or synthesized sound
   What is your preference in 'acousticness'? "

   Let's say, you have 0.00242 for acousticness.

   If you type **8** for acousticness, it will get adjusted to 0.30242, a higher number.

   MelodyMystique will use these adjusted audio features number to generate a more personalized playlist for you.
   In the example here, you will get tracks that have more acoustic instruments like guitars, pianos, or live vocals.

   If you type **5** (so you position the audio feature in a scale in a neutral position) for acousticness, the mean value
   for that won't change from 0.00242.

> [!IMPORTANT]
> It's not asking you to rank each audio feature in relation to each other.

12. You will get information about your top (max 10) artists based on your chosen playlist or recently played tracks.
You will see their names, and how many tracks they are in.
The playlist generation will be based on these artists and the adjusted mean values for the audio features.
13. Choose If you want to include any of these artist's songs in your personalized playlist. Hit `Enter`.

> [!IMPORTANT]
> Even If you choose to exclude the artists from the personalized playlist, the generation of the
playlist will still be\
based on these artists, but the personalized playlist won't have tracks from these artists.

14. Type a name for the generated playlist (max 150 characters long).
15. Check your spotify account for the generated playlist.

## Set up your Spotify API credentials:
<a name="set-up-your-spotify-api-credentials"></a>

How to set up your Spotify API credentials:
### 1. Create a Spotify Developer account and create a new app.
   * Open [this link](https://developer.spotify.com/) and `log in` to your Spotify account.
   * In to top right corner, click on to your profile name, and select the `Dashboard` option.
   * Then click to the `Create app` button.
   * Here you should fill in:
     * **App name** (enter any character)
     * **App description** (enter any character)
     * **Redirect URI** with `http://localhost:3000/callback`
   * In the "Which API/SDKs are you planning to use?" **Tick the `Web API` checkbox.**
   * Finally, **tick the `Terms of Service` checkbox.** and click `Save`
### 2. Getting the API credentials:
   * In the newly opened page, you are inside the app that you created a moment ago.
   * Click to the `Settings` button.
   * Here you can find the **Client ID.**
   * Click to the `View client secret` option to get the **Client secret**.
### 3. Add your Client ID and Client secret to the `config.py` file.
   * CLIENTID = 'your_client_id'
   * CLIENTSECRET = 'your_client_secret'

## How it works?
<a name="how-it-works"></a>
### Code structure:
#### Project.py contains 3 classes:
* #### Auth Class (2 functions)
  * Get the access token
  * Handles the authentication

* #### SpotifyAPI Class (11 functions)
  * Contains all the Spotipy code for the API requests.

* #### SpotifyPlaylist Class (16 functions)
  * Get the inputs from the user and validate them
  * Printing out the top artists
  * Handle multiple API requests
  * Filter out tracks
  * Encode the playlist cover photo to base 64 format
  * Wait for the cover photo to be uploaded


* #### Outside the classes, there are 3 functions:
  * `login()` - Initiate the Spotify authentication
  * `callback()` - It grabs the access token, then with the Functools and concurrent.futures module it starts
  a new thread that calls the primary function.
  * `primary_func(response_code)` - Callback endpoint to handle the authorization response, here we
  initiate the whole project.

### Description of functionality:
#### Authentication Flow
1. The user is presented with a welcome message.
2. The user accesses the authentication page by visiting http://localhost:3000 (`login()`).
3. The authentication process is initiated by redirecting to Spotify's authentication page.
4. After granting access, the user is redirected to the callback endpoint (/callback) with an authorization code
(`callback()`).
5. The authorization code is used to obtain an access token from Spotify.
6. The access token is stored, allowing MelodyMystique to interact with the Spotify API.

#### Playlist Analysis
1. The user chooses a playlist or recently played tracks for analysis (`get_playlists()`,
`get_recently_or_playlist()`).
2. The application retrieves the selected tracks and their audio features using the Spotify API (`get_tracks()`,
`get_track_audio_features()`).
3. The user provides preferences for each audio feature on a scale of 0 to 10 (`get_user_preferences()`).
4. MelodyMystique calculates adjusted mean values for each audio preference based on user input (`adjust_mean()`).
5. Top artists from the selected tracks are identified (`get_user_top_artists()`).
6. The user decides whether to include or exclude these top artists in the personalized playlist (`get_user_input()`).
7. MelodyMystique generates track recommendations based on the adjusted user preferences and top artists
(`recommended_tracks()`).
8. Filtering out the recommended tracks:

   MelodyMystique filters out recommended tracks that are in the chosen analyzed playlist or in the recently
   played tracks (`filter_tracks()`).

   When the user chooses to exclude top artists (`artist_inclusion == 'N'`):
    * MelodyMystique also excludes recommended tracks that are from the top artists (`exclude_top_artists()`).
9. Users specify the name for the new personalized playlist (`get_user_input()`).

#### Playlist Creation
1. MelodyMystique creates a new public playlist on the user's Spotify account (`create_playlist()`).
2. The recommended tracks are added to the newly created playlist (`add_tracks_to_playlist()`).
3. A random cover photo is chosen and uploaded as the playlist's cover image (`get_playlist_imagebase64()`,
`wait_for_playlist_cover_to_be_uploaded()`).
4. The user is informed that the personalized playlist has been generated successfully.

## Authors:
### Mariann Ács-Kovács

#### [LinkedIn profile](https://www.linkedin.com/in/mariann-%C3%A1cs-kov%C3%A1cs-10032b299/)


## License

This project is licensed under the MIT License - see the LICENSE.txt file for details
