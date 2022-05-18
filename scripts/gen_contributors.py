import os
import json
import traceback
import requests

try:
    fetch = requests.get(
        "https://api.github.com/repos/joaorb64/StreamHelperAssets/contributors?anon=1")
    contributors = json.loads(fetch.text)

    contributors_final = []

    for c in contributors:
        # Skip buildbot
        if c.get("name") == "Buildbot":
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
