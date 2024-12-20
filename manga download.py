import requests # type: ignore
import json
from pathlib import Path
import time
import math

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
    limit = response.json()['limit']
    total = response.json()['total']
    pages = total/limit
    pages = math.ceil(pages)
    data=response.json()['data']
    chapterIDs = {}
    chapterList=[]
    # print('data = '+str(response.json()))
    # print('data length = '+str(len(data)))
    for j in range(pages):
        # print('j = '+str(j))
        for i in data:
            # print('data[i] = '+str(i))
            if i['type'] == 'chapter' and i['attributes']['translatedLanguage'] == 'en':
                chapterIDs.update({i['attributes']['chapter']:i['id']})
                chapterList.append(i['attributes']['chapter'])
                # print(i['attributes']['chapter'])
                # print('updated chapterList with chapter number: '+i['attributes']['chapter'])
        # print('chapterList = '+str(chapterList))
        # print('chapterIDs = '+str(chapterIDs))
        j = j+1
        dead = False
        while not dead:
            url = 'https://api.mangadex.org/manga/'+mangaID+'/feed?includeFuturePublishAt=0&includeExternalUrl=0&includeEmptyPages=0&offset='+str(j*limit)
            payload = {}
            headers = {}
            response = requests.request("GET", url, headers=headers, data=payload)
            try:
                data=response.json()['data']
                dead = True
                # print('j = '+str(j))
                print('fetched chapter ID page '+str(j)+' out of '+str(pages))
            except:
                print('fetching chapter ID failed, trying again..')
                time.sleep(5)
                # print(url)
                # print(response.status_code)
                # print(response.json())

    return(chapterIDs,chapterList)

# input chapterID
#return List of download URL
def getDownloadURL(chapterID):
    dead = False
    while not dead:
        url = 'https://api.mangadex.org/at-home/server/'+chapterID

        payload = {}
        headers = {}

        response = requests.request("GET", url, headers=headers, data=payload)
        try:
            response=response.json()
            baseURL=response['baseUrl']
            hash=response['chapter']['hash']
            data=response['chapter']['data']
            URLs=[]
            for i in data:
                url=baseURL+'/data/'+hash+'/'+i
                URLs.append(url)
            dead = True
            return(URLs)
        except:
            print('Parsing error, trying again..')
            time.sleep(5)

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
    dead = False
    while not dead:
        try:
            response = requests.get(url, timeout=10)
            dead = True
        except requests.exceptions.Timeout:
            print('Timed out, retrying...')
        except requests.exceptions.ConnectionError:
            print('Connection error, retrying in 10 seconds..')
            time.sleep(10)
    file_Path = path

    if response.status_code == 200:
        with open(file_Path, 'wb+') as file:
            file.write(response.content)
        print('File downloaded successfully')
    else:
        print('Failed to download file')
        raise Exception('sometingwong with downloading the url')


ListID="<LIST ID>"
token=login('<USERNAME>','<PASSWORD>')

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

    print(mangaName + ' --> '+str(chapterList))
    for i in chapterList:
        chapterID=chapterIDs[i]
        with open('log.json', 'r') as openfile:
            log = json.load(openfile)
        loggedChapters=log[mangaID]
        if i in loggedChapters:
            print(mangaName+' chapter '+str(i)+' already downloaded (from log)')
        else:
            downloadURL=getDownloadURL(chapterID)
            count=1
            for url in downloadURL:
                cwd = Path.cwd()
                sub = Path(mangaName1)
                if i == None:
                    sub1 = Path('Oneshot')
                else:
                    sub1 = Path(str(i))
                file = Path(str(count)+'.png')
                count=count+1
                paf = cwd / sub / sub1
                try:
                    paf.mkdir(parents=True)
                except FileExistsError:
                    print('FileExistsError')
                paf = paf / file
                if i == None:
                    print(mangaName+' chapter Oneshot')
                else:
                    print(mangaName+' chapter '+i) 
                print(url)
                download(paf,url)
            loggedChapters.append(i)
            log[mangaID]=loggedChapters
            with open("log.json", "w") as outfile:
                json.dump(log, outfile)
