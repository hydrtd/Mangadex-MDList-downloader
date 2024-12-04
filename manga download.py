import requests # type: ignore
import json
import urllib.request
import os
from pathlib import Path
import time

# input username, password
# return access token (str)
def login(user,pw):
    url = "https://auth.mangadex.org/realms/mangadex/protocol/openid-connect/token"
    payload = 'grant_type=password&username='+user+'&password='+pw+'&client_id=personal-client-57159ffb-0a54-4814-a033-8b4b8ff17daa-71a87915&client_secret=esZmpIL6L1J51nNMFAPEfT39tn55lKA2'
    headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    # parse this shit
    access_token = response.json()["access_token"]
    return(access_token)

# input access token, List ID
# return List of manga IDs of all manga in list
def getList(access_token,ListID):
    url = "https://api.mangadex.org/list/" + ListID

    payload = {}
    headers = {
    'Authorization': 'Bearer ' + access_token
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    # print(response.text)

    # parse the response
    response = response.json()["data"]["relationships"]
    # print(response)
    mangaIDs = []
    for i in response:
        # print(str(i))
        if i["type"] == 'manga':
            mangaIDs.append(i['id'])
    return(mangaIDs)

# input manga ID
# return dict {Chapter# : ChapterID} and List of all chapter#
def getChapterID(mangaID):
    url = 'https://api.mangadex.org/manga/'+mangaID+'/feed?includeFuturePublishAt=0&includeExternalUrl=0&includeEmptyPages=0'

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    data=response.json()['data']
    chapterIDs = {}
    chapterList=[]
    for i in data:
        if i['type'] == 'chapter' and i['attributes']['translatedLanguage'] == 'en':
            chapterIDs.update({i['attributes']['chapter']:i['id']})
            chapterList.append(i['attributes']['chapter'])
    return(chapterIDs,chapterList)

# input chapterID
#return List of download URL
def getDownloadURL(chapterID):
    url = 'https://api.mangadex.org/at-home/server/'+chapterID

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    response=response.json()
    baseURL=response['baseUrl']
    hash=response['chapter']['hash']
    data=response['chapter']['data']
    URLs=[]
    for i in data:
        url=baseURL+'/data/'+hash+'/'+i
        URLs.append(url)
    return(URLs)

# input Manga ID
# return name of the manga
def getMangaName(mangaID):
    url = "https://api.mangadex.org/manga/" + mangaID

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    name=response.json()["data"]["attributes"]["title"]["en"]
    return(name)

# input file path, download url
# return nothing.
def download(path,url):
    response = requests.get(url)
    file_Path = path

    if response.status_code == 200:
        with open(file_Path, 'wb+') as file:
            file.write(response.content)
        print('File downloaded successfully')
    else:
        print('Failed to download file')
        raise Exception('sometingwong with downloading the url')


ListID=<MDLIST ID>
token=login(<USERNAME>,<PASSWORD>)
cooldown=5

mangaList=getList(token,ListID)
for mangaID in mangaList:
    mangaName=getMangaName(mangaID)
    mangaName1=mangaName
    for char in r'\/:*?"<>|':
        mangaName1=mangaName1.replace(char,'')
    chapterIDs,chapterList=getChapterID(mangaID)
    #open log
    with open('log.json', 'r') as openfile:
        log = json.load(openfile)
    if str(log).find(mangaID) == -1:
        #update with mangaID:list of dl'd chapters
        log.update({mangaID:[]})
        #write to log
        with open("log.json", "w") as outfile:
            json.dump(log, outfile)

    for i in chapterList:
        chapterID=chapterIDs[str(i)]
        with open('log.json', 'r') as openfile:
            log = json.load(openfile)
        loggedChapters=log[mangaID]
        if i in loggedChapters:
            print(mangaName+' chapter '+str(i)+' already downloaded (from log)')
        else:
            downloadURL=getDownloadURL(chapterID)
            count=1
            for url in downloadURL:
                time.sleep(cooldown)
                cwd = Path.cwd()
                sub = Path(mangaName1)
                sub1 = Path(str(i))
                file = Path(str(count)+'.png')
                count=count+1
                paf = cwd / sub / sub1
                try:
                    paf.mkdir(parents=True)
                except FileExistsError:
                    print('FileExistsError')
                paf = paf / file
                print(mangaName+' chapter '+i)
                print(url)
                download(paf,url)
            loggedChapters.append(i)
            log[mangaID]=loggedChapters
            with open("log.json", "w") as outfile:
                json.dump(log, outfile)
