import os
import json
import traceback
import requests

try:
    fetch = requests.get(
        "https://api.github.com/repos/joaorb64/StreamHelperAssets/contributors?anon=1")
    contributorsAssets = json.loads(fetch.text)

    fetch = requests.get(
        "https://api.github.com/repos/joaorb64/TournamentStreamHelper/contributors?anon=1")
    contributorsTool = json.loads(fetch.text)

    contributors_final = []

    for c in contributorsTool:
        # Skip buildbot and actions-user
        if c.get("name") == "Buildbot" or c.get("login") == "actions-user":
            continue
        if c.get("login"):
            contributors_final.append(c.get("login"))
        elif c.get("name"):
            contributors_final.append(c.get("name"))

    for c in contributorsAssets:
        # Skip buildbot
        if c.get("name") == "Buildbot":
            continue
        # Do not add duplicates
        if c.get("name") in contributors_final or c.get("login") in contributors_final:
            continue
        if c.get("login"):
            contributors_final.append(c.get("login"))
        elif c.get("name"):
            contributors_final.append(c.get("name"))

    # Add extra contributors that didn't commit to the repo
    contributors_final.extend([
        "@kipferlkipferl",
        "@Luiro_",
        "@wl_mint"
    ])

    with open("assets/contributors.txt", 'w') as out:
        out.writelines("\n".join(contributors_final))
except:
    print(traceback.format_exc())
