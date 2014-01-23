#!/usr/bin/env python
from multiprocessing import Process
import time
import sys
import os
import praw

#TODO make the comment fetching and analysis on a different threads
# You can do this!

#TODO make it run as secure server for remote control
# Probably more difficult

__author__="Sumner"
__version__="0.9.2.1"
USER_AGENT = "Antiracism_Bot by /u/Renmusxd"
DEFAULT_CREDENTIAL_FILE = "credentials.txt"
DEFAULT_RACISM_FILE = "racist.txt"
DEFAULT_RACE_FILE = "races.txt"
DEFAULT_REPLIED_FILE = "replied.txt"
DEFAULT_NETWORK_LIMIT = 1000000000L # May be subject to change

class RacismChecker(object):
    '''
    Finds racism on the internet
    '''
    def __init__(self,username,password,racismPhraseFilePath,raceFilePath,repliedFilePath,verbose=False,reply=True):
        self.verbose = verbose
        if self.verbose:print("[*] Antiracism_Bot v."+__version__)
        if self.verbose:print("[+] Initialising new Bot")
        if self.verbose:print("[*] Verbose mode activated")
        self.reply = reply
        if self.verbose:
            if reply:
                print("[*] Bot will reply")
            else:
                print("[*] Bot will not reply")
        self.running = True
        self.r = praw.Reddit(USER_AGENT)
        self.username = username
        if self.verbose:print("[*] Logging in as "+username)
        try:
            self.r.login(username,password)
            if self.verbose:print("[+] Login successful")
        except:
            if self.verbose:
                print("[!] Login failed")
                print("[*] Setting reply to false")
                self.reply = False
            
        self.racismFilePath = racismPhraseFilePath
        self.raceFilePath = raceFilePath
        self.repliedFilePath = repliedFilePath
        self.racismKeyPhrases = {} # racistPhrase:reason
        self.races = []
        if self.verbose:print("[*] Populating racism table")
        self.populateRacismDict()
        if self.verbose:print("[*] Racist table contains "+str(len(self.racismKeyPhrases))+" entries")
        self.alreadyDone = set()
        if self.verbose:print("[*] Reading previously made comments")
        self.readAlreadyDone()
        self.todo = {}
        
    def shutDown(self):
        self.saveAlreadyDone()
        this.running = False
        
    def populateRacismDict(self):
        '''
        Fills table from files
        '''
        racismTable = {}
        if self.verbose:print("\t[*] Reading "+self.raceFilePath)
        with open(self.raceFilePath) as raceFile:
            for raceLine in raceFile:
                raceLine = raceLine.strip()
                self.races.append(raceLine)
        if self.verbose:print("\t[*] Race file contains "+str(len(self.races))+" races")
        if self.verbose:print("\t[*] Reading "+self.racismFilePath)
        with open(self.racismFilePath) as racismFile:
            for racismLine in racismFile:
                # Space on each side should prevent [jap]anese from alert
                racismLine = racismLine.strip()
                if racismLine.find(":")>-1:
                    reason = racismLine[:racismLine.find(":")]
                    racismLine = racismLine[racismLine.find(":")+1:]
                    if "[RACE]" in racismLine:
                        recRacismTable = self.raceRecursion(racismLine)
                        for phrase in recRacismTable:
                            racismTable[phrase.lower()] = reason.lower()
                    else:
                        # ALL LOWER CASE!
                        racismTable[racismLine.lower()] = reason.lower()
                else:
                    if self.verbose:print("\t[!] Failed to parse: "+racismLine)
        if self.verbose:print("\t[*] Constructed "+str(len(racismTable))+" racist phrases")
        self.racismKeyPhrases = racismTable
                    
    def raceRecursion(self,line):
        '''
        Through recursion should replace all [RACE]s with all permutations
        '''
        newRaceLineTable = []
        if "[RACE]" in line:
            for race in self.races:
                    newLine = line.replace("[RACE]", race, 1) # removes 1 [RACE] token
                    if "[RACE]" in newLine:
                        newRaceLineTable = newRaceLineTable + self.raceRecursion(newLine)
                    else:
                        newRaceLineTable.append(newLine)
        return newRaceLineTable
    
    def subredditLoop(self,subredditName):
        '''
        Check specific subreddit(s) for racism
        '''
        if self.verbose:print("[*] Checking subreddits: "+subredditName)
        while self.running:
            subreddit = self.r.get_subreddit(subredditName)
            subredditComments = subreddit.get_comments(limit=None)
            self.commentLoop(subredditComments)
            self.manageTODOs()
            self.saveAlreadyDone()    
            time.sleep(2)
                    
    def allLoop(self):
        '''
        Check everything for racism
        '''
        if self.verbose:print("[*] Checking all subreddits")
        while self.running:
            all_comments = self.r.get_comments("all",limit=None)
            self.commentLoop(all_comments)
            self.manageTODOs()
            self.saveAlreadyDone()
            time.sleep(2)
    
    def manageTODOs(self):
        for comment, replyText in self.todo.iteritems():
            try:
                comment.reply(replyText)
                if self.verbose:print("[*] Replied to comment "+comment.id+":\n"+replyText)
                self.alreadyDone.add(comment.id)
                self.todo.remove(comment)
            except praw.errors.RateLimitExceeded:
                return
    
    def readAlreadyDone(self):
        with open(self.repliedFilePath) as repFile:
            for line in repFile:
                line = line.strip()
                if line!="":
                    self.alreadyDone.add(line)
    
    def saveAlreadyDone(self):
        with open(self.repliedFilePath,"w") as repFile:
            for a in self.alreadyDone:
                repFile.write("\n"+a)
    
    def commentLoop(self,comments):
        for comment in comments:
            (commentisracist, quotes) = self.checkIfCommentIsRacist(comment.body.lower())
            if commentisracist and comment.author.name.lower()!=self.username.lower() and comment.id not in self.alreadyDone and comment not in self.todo:
                if self.verbose:
                    print("[*] Found racist comment: "+comment.id)
                    print("[*] "+comment.body.strip())
                replyText = "Your comment contains "
                reasonDict = {}
                for quote in quotes:
                    reason = self.racismKeyPhrases[quote]
                    if reason in reasonDict:
                        reasonDict[reason]+=1
                    else:
                        reasonDict[reason]=1
                # Make sentence based on racism
                for racismReason, count in reasonDict.iteritems():
                    replyText+=racismReason+"("+str(count)+"), "
                replyText = replyText[:-2]+"!  \n\n  "
                i=1
                for quote in quotes:
                    replyText+="\t"+str(i)+". "+quote+"\n\n"
                    i+=1
                if self.verbose:
                    for racismReason, count in reasonDict.iteritems():
                        print("\t-"+racismReason)
                try:
                    if self.reply:
                        comment.reply(replyText)
                        if self.verbose:print("\t[+] Replied: "+replyText)
                    else:
                        if self.verbose:print("\t[*] Would reply:\n\t"+replyText)
                    self.alreadyDone.add(comment.id)
                except praw.errors.RateLimitExceeded as e:
                    if self.verbose:
                        print("\t[!] Cannot reply: Ratelimit Error")
                        print("\t[*] "+e.message)
                        print("\t[*] Adding comment to TODO set")
                        self.todo[comment] = replyText
                    
    def checkIfCommentIsRacist(self,commentText):
        '''
        Checks if a comment(string) is racist, returns (boolean,List)
        '''
        commentText = commentText.lower()
        racistCommentList = []
        for racistComment in self.racismKeyPhrases:
            while True:
                racistLocation = commentText.find(racistComment.lower())
                if racistLocation>-1: #additional tests
                    passedTests = False
                    if racistLocation==0:
                        if commentText[len(racistComment)].isspace():
                            passedTests = True
                    elif racistLocation+len(racistComment)==len(commentText):
                        if commentText[racistLocation-1].isspace():
                            passedTests = True
                    else:
                        if commentText[racistLocation-1].isspace() and commentText[racistLocation+len(racistComment)].isspace():
                            passedTests = True
                    if passedTests:
                        commentText = commentText.replace(racistComment.lower(),"",1)
                        racistCommentList.append(racistComment)
                else:
                    break
        if len(racistCommentList)>0:
            return (True,racistCommentList)
        return (False,None)

def getCredentials(fileName):
    '''
    Gets credentials from file
    '''
    username = ""
    password = ""
    with open(fileName) as credFile:
        for line in credFile:
            line = line.strip()
            if "username:" in line:
                line = line.replace("username:","")
                username = line
            elif "password:" in line:
                line = line.replace("password:","")
                password = line
    return (username,password)

def startThreadsAll(bot):
    p1 = Process(target=serverHandler)
    p2 = Process(target=networkHandler,args=())
    p3 = Process(target=bot.allLoop)
    p1.start()
    p2.start()
    p3.start()
    p3.join()
    
def startThreadsSubreddit(bot,subredditString):
    p1 = Process(target=serverHandler)
    p2 = Process(target=networkHandler)
    p3 = Process(target=bot.subredditLoop,args=(subredditString,))
    p1.start()
    p2.start()
    p3.start()
    p3.join()
    
def serverHandler():
    #TODO communicate with clients
    pass

def networkHandler(limit,bot,focus=None,verbose=False):
    managing = True
    try:
        while managing:
            sleep(300)
            netinfo = psutil.network_io_counters(pernic=True)
            totalusage = 0
            if focus in netinfo:
                focusNetInfo = netinfo[focus]
                totalusage = focusNetInfo.bytes_sent + focusNetInfo.bytes_recv
            else:
                for key,focusNetInfo in netinfo.iteritems():
                    totalusage += focusNetInfo.bytes_sent + focusNetInfo.bytes_recv
            if totalusage>limit:
                if verbose:
                    print("[!] Total network usage exceeded max")
                    print("\t"+str(totalusage)+"/"+str(limit))
                    print("[!] Shutting down")
                bot.shutDown()
                managing = False
            if verbose:
                if focus in netinfo:
                    print("[*] Total network usage on "+focus+": "+str(totalusage))
                else:
                    print("[*] Total network usage: "+str(totalusage))
                    
    except Exception as e:
        if verbose:print("[!] Exception encountered, shutting down")
        bot.shutDown()
        raise e

if __name__ == "__main__":
    mypath = os.path.dirname(os.path.realpath(__file__))
    DEFAULT_CREDENTIAL_FILE = mypath+"/"+DEFAULT_CREDENTIAL_FILE
    DEFAULT_RACISM_FILE = mypath+"/"+DEFAULT_RACISM_FILE
    DEFAULT_RACE_FILE = mypath+"/"+DEFAULT_RACE_FILE
    DEFAULT_REPLIED_FILE = mypath+"/"+DEFAULT_REPLIED_FILE
    try:
        isverbose = False
        doesreply = True
        if "-help" in sys.argv:
            print("Usage: python antiracism_bot.py <flags> [subreddits/all]")
            print("Flags\t\tActions")
            print("-v\t\tVerbose mode")
            print("-d\t\tNo replies")
            print("-e\t\tExample crash report")
        else:
            if "-v" in sys.argv:
                isverbose = True
                sys.argv.remove("-v")
            if "-d" in sys.argv:
                doesreply = False
                sys.argv.remove("-d")
            if "-e" in sys.argv:
                raise Exception("Example exception")
            # parse for subreddits
            #suitable for flags
            (username, password) = getCredentials(DEFAULT_CREDENTIAL_FILE)
            args = sys.argv
            if len(args)>1 and not "all" in args:
                racismChecker = RacismChecker(username, password,DEFAULT_RACISM_FILE,DEFAULT_RACE_FILE,DEFAULT_REPLIED_FILE,verbose=isverbose,reply=doesreply)
                # args[0] is filename (should not be run in interpreter)
                subredditString = args[1]
                for sub in args[2:]:
                    subredditString += "+"+sub
                if isverbose:print("[*] Starting threads")
                startThreadsSubreddit(racismChecker,subredditString)
            elif len(args)>1 and "all" in args:
                racismChecker = RacismChecker(username, password,DEFAULT_RACISM_FILE,DEFAULT_RACE_FILE,DEFAULT_REPLIED_FILE,verbose=isverbose,reply=doesreply)
                if isverbose:print("[*] Starting threads")
                startThreadsAll(racismChecker)
            else:
                print("Type '-help' for help")
    except Exception as e:
        r = praw.Reddit("Crashreport bot by /u/Renmusxd")
        username = ""
        password = ""
        with open(DEFAULT_CREDENTIAL_FILE) as credFile:
            for line in credFile:
                line = line.strip()
                if "username:" in line:
                    line = line.replace("username:","")
                    username = line
                elif "password:" in line:
                    line = line.replace("password:","")
                    password = line
        print("[!] Crashed with exception:\n"+str(type(e))+"\n\n"+e.message)
        print("[!] Attempting to send message to Renmusxd")
        try:
            r.login(username,password)
            r.send_message("Renmusxd","Crash report for Antiracism_Bot","Crashed with exception:\n"+str(type(e))+"\n\n"+e.message)
            print("[+] Crash report sent sucessfully")
        except Exception as e:
            print("[!] Exception while sending report, sorry. There's nothing more I can do.")