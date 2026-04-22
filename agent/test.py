from trello_reader import get_all_lists, get_cards_in_list
lists = get_all_lists()
print("Board lists found:")

for l in lists:
    print(f"  - {l['name']} (id: {l['id'][:8]}...)")

cards = get_cards_in_list("Backlog")
print(f"Cards in Backlog: {len(cards)}")