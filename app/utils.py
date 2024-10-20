import requests
import logging
import os

def update_plex_preroll(plex_token, plex_base_url, pre_roll_path):
    """
    Updates the Plex pre-roll setting via the Plex API.
    
    Parameters:
    - plex_token: Your Plex API token.
    - plex_base_url: Base URL of your Plex server.
    - pre_roll_path: The file path to the pre-roll video.
    """
    url = f"{plex_base_url}/:/prefs?CinemaTrailersPrerollID={pre_roll_path}&X-Plex-Token={plex_token}"
    try:
        response = requests.put(url, verify=False)  # verify=False if using self-signed cert
        if response.status_code == 200:
            logging.info("Pre-roll updated successfully.")
        else:
            logging.error(f"Failed to update pre-roll: {response.status_code} - {response.content}")
    except Exception as e:
        logging.error(f"Exception occurred while updating pre-roll: {e}")
