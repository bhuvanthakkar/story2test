import requests
import os
from dotenv import load_dotenv

load_dotenv()

TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_TOKEN   = os.getenv("TRELLO_TOKEN")
TRELLO_BOARD_ID = os.getenv("TRELLO_BOARD_ID")
BASE_PARAMS    = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}


def get_all_lists():
    """Return all lists on the board"""
    url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/lists"
    response = requests.get(url, params=BASE_PARAMS)
    response.raise_for_status()
    return response.json()


def get_cards_in_list(list_name: str) -> list:
    """Fetch all open cards from a named list"""
    lists = get_all_lists()
    target = next((l for l in lists if l["name"] == list_name), None)
    if not target:
        raise ValueError(f"List '{list_name}' not found on board. "
                         f"Available lists: {[l['name'] for l in lists]}")

    url = f"https://api.trello.com/1/lists/{target['id']}/cards"
    response = requests.get(url, params=BASE_PARAMS)
    response.raise_for_status()
    return response.json()   # list of card dicts


def post_comment(card_id: str, text: str):
    """Post a comment on a card"""
    url = f"https://api.trello.com/1/cards/{card_id}/actions/comments"
    response = requests.post(url, params=BASE_PARAMS, data={"text": text})
    response.raise_for_status()
    return response.json()


def move_card(card_id: str, target_list_name: str):
    """Move a card to a different list"""
    lists = get_all_lists()
    target = next((l for l in lists if l["name"] == target_list_name), None)
    if not target:
        raise ValueError(f"List '{target_list_name}' not found")

    url = f"https://api.trello.com/1/cards/{card_id}"
    response = requests.put(url, params=BASE_PARAMS,
                            data={"idList": target["id"]})
    response.raise_for_status()


def add_label(card_id: str, color: str = "red"):
    """Add a coloured label to a card (e.g. red = blocker)"""
    url = f"https://api.trello.com/1/cards/{card_id}/labels"
    requests.post(url, params=BASE_PARAMS, data={"color": color})