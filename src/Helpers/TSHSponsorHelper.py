import os
import re
from ..StateManager import StateManager

class TSHSponsorHelper:

    def ExportValidSponsors(team: str, path: str):
        sponsor_logo= None
        cleaned_sponsor = re.sub(r"[,/|;:<>\\?*]", "_", team)
        if os.path.exists(f"./user_data/sponsor_logo/{cleaned_sponsor.upper()}.png"):
            sponsor_logo = f"./user_data/sponsor_logo/{cleaned_sponsor.upper()}.png"
            StateManager.Unset(f"{path}.sponsor_logos")
        else:
            split_sponsor = re.split(r"[,/|;: <>\\?*]", team)
            i: int = 0
            for sponsor in split_sponsor:
                if os.path.exists(f"./user_data/sponsor_logo/{sponsor.upper()}.png"):
                    if sponsor_logo is None:
                        sponsor_logo = f"./user_data/sponsor_logo/{sponsor.upper()}.png"
                    StateManager.Set(f"{path}.sponsor_logos.{i+1}", f"./user_data/sponsor_logo/{sponsor.upper()}.png")
                    i =+ 1
                    
        if sponsor_logo is not None:
            StateManager.Set(f"{path}.sponsor_logo", sponsor_logo)
        else:
            StateManager.Unset(f"{path}.sponsor_logo")
            StateManager.Unset(f"{path}.sponsor_logos")