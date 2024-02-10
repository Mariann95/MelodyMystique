import pytest
from project import SpotifyPlaylist, SpotifyAPI


@pytest.fixture
def spotify_api_instance():
    return SpotifyAPI()


@pytest.fixture
def spotify_playlist_instance(spotify_api_instance):
    return SpotifyPlaylist(spotify_api_instance)


def test_filter_recommendations_include_artists(spotify_playlist_instance, artist_included='Y'):
    recommendations = [
        {"id": "1", "artists": [{"id": "artist1"}, {"id": "artist2"}]},
        {"id": "2", "artists": [{"id": "artist3"}, {"id": "artist4"}]},
        {"id": "3", "artists": [{"id": "artist5"}]},
        {"id": "4", "artists": [{"id": "artist2"}]},
        {"id": "5", "artists": [{"id": "artist6"}]}
    ]
    track_ids = ["2", "5"]

    if artist_included == 'Y':
        filtered_tracks = spotify_playlist_instance.filter_tracks(recommendations, track_ids)
        assert set(filtered_tracks) == {"4", "3", "1"}


def test_filter_recommendations_exclude_artists(spotify_playlist_instance, artist_included='N'):
    artists_to_delete = ["artist2", "artist3"]
    recommendations = [
        {"id": "1", "artists": [{"id": "artist1"}, {"id": "artist2"}]},
        {"id": "2", "artists": [{"id": "artist3"}, {"id": "artist4"}]},
        {"id": "3", "artists": [{"id": "artist5"}]},
        {"id": "4", "artists": [{"id": "artist2"}]},
        {"id": "5", "artists": [{"id": "artist6"}]}
    ]
    track_ids = ["2", "5"]

    if artist_included == 'N':
        remaining_tracks = spotify_playlist_instance.exclude_top_artists(artists_to_delete, recommendations)
        assert remaining_tracks == [
            {"id": "3", "artists": [{"id": "artist5"}]},
            {"id": "5", "artists": [{"id": "artist6"}]}
        ]
        filtered_tracks = spotify_playlist_instance.filter_tracks(remaining_tracks, track_ids)
        assert filtered_tracks == ["3"]


def test_adjust_mean_positive(spotify_playlist_instance):
    user_preference = 8
    original_mean = 0.6
    adjusted_mean = spotify_playlist_instance.adjust_mean(user_preference, original_mean)
    assert adjusted_mean == 0.9


def test_adjust_mean_negative(spotify_playlist_instance):
    user_preference = 2
    original_mean = 0.6
    adjusted_mean = spotify_playlist_instance.adjust_mean(user_preference, original_mean)
    assert adjusted_mean == 0.3


def test_adjust_mean_tempo(spotify_playlist_instance):
    user_preference = 6
    original_mean = 110
    adjusted_mean = spotify_playlist_instance.adjust_mean(user_preference, original_mean)
    assert adjusted_mean == 120


def test_adjust_mean_reach_min(spotify_playlist_instance):
    user_preference = 1
    original_mean = 0.2
    adjusted_mean = spotify_playlist_instance.adjust_mean(user_preference, original_mean)
    assert adjusted_mean == 0


def test_adjust_mean_reach_max(spotify_playlist_instance):
    user_preference = 9
    original_mean = 0.8
    adjusted_mean = spotify_playlist_instance.adjust_mean(user_preference, original_mean)
    assert adjusted_mean == 1


if __name__ == '__main__':
    pytest.main()
