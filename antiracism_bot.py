#!/usr/bin/env python
from RacismDataStructure import DataStructure
from threading import Thread
import string
import time
import sys
import os
import praw
import unicodedata
import psutil
import socket
import SocketServer

#TODO make it run as secure server for remote control
# Probably more difficult

#TODO improve ability to avoid false positives
# he said/they think
# good versus bad words

__author__="Sumner"
__version__="0.9.5.1"
USER_AGENT = "Antiracism_Bot by /u/Renmusxd"
DEFAULT_CREDENTIAL_FILE = "credentials.txt"
DEFAULT_RACISM_FILE = "racist.txt"
DEFAULT_RACE_FILE = "races.txt"
DEFAULT_REPLIED_FILE = "replied.txt"
DEFAULT_NETWORK_LIMIT = 1000000000L # May be subject to change

#sys.argv = ["antiracism_bot.py","-v","test"]

class RacismChecker(object):
    '''
    Finds racism on the internet
    '''
    def __init__(self,username,password,racismPhraseFilePath,raceFilePath,repliedFilePath,verbose=False,reply=True):
        self.verbose = verbose
        if self.verbose:print("[*] Antiracism_Bot v."+__version__)
        if self.verbose:print("[*] Initialising new Bot")
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
        self.racismKeyPhrases = {} # racistPhrase:(reason,value)
        self.races = []
        if self.verbose:print("[*] Populating racism table")
        self.populateRacismDict()
        if self.verbose:print("[*] Racist table contains "+str(len(self.racismKeyPhrases))+" entries")
        self.alreadyDone = set()
        if self.verbose:print("[*] Reading previously made comments")
        self.readAlreadyDone()
        self.todo = DataStructure()
        self.todoIDs = []
        
    def shutdown(self):
        self.saveAlreadyDone()
        self.running = False
        
    def populateRacismDict(self):
        '''
        Fills table from files
        '''
        racismTable = {}
        if self.verbose:print("\t[*] Reading "+self.raceFilePath)
        with open(self.raceFilePath) as raceFile:
            for raceLine in raceFile:
                raceLine = raceLine.strip()
                if raceLine[0]!="#":
                    self.races.append(raceLine)
        if self.verbose:print("\t[*] Race file contains "+str(len(self.races))+" races")
        if self.verbose:print("\t[*] Reading "+self.racismFilePath)
        with open(self.racismFilePath) as racismFile:
            for racismLine in racismFile:
                # Space on each side should prevent [jap]anese from alert
                racismLine = racismLine.strip()
                if racismLine[0]!="#":
                    if racismLine.find(":")>-1:
                        value = int(racismLine[:racismLine.find(":")])
                        racismLine = racismLine[racismLine.find(":")+1:]
                        reason = racismLine[:racismLine.find(":")]
                        racismLine = racismLine[racismLine.find(":")+1:]
                        if "[RACE]" in racismLine:
                            recRacismTable = self.raceRecursion(racismLine)
                            for phrase in recRacismTable:
                                racismTable[phrase.lower()] = (reason.lower(),value)
                        else:
                            # ALL LOWER CASE!
                            racismTable[racismLine.lower()] = (reason.lower(),value)
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
        Check specific subreddit(s) for racism and replies
        '''
        if self.verbose:print("[*] Checking subreddits: "+subredditName)
        while self.running:
            try:
                subreddit = self.r.get_subreddit(subredditName)
                subredditComments = subreddit.get_comments(limit=None)
                self.commentLoop(subredditComments)
                self.manageTODOs()
                self.saveAlreadyDone()    
                time.sleep(2)
            except Exception as e:
                if self.verbose:print("[!] Exception: "+e.message)
                reportException(e)
                    
    def allLoop(self):
        '''
        Check everything for racism
        '''
        if self.verbose:print("[*] Checking all subreddits")
        while self.running:
            try:
                all_comments = self.r.get_comments("all",limit=None)
                self.commentLoop(all_comments)
                self.manageTODOs()
                self.saveAlreadyDone()
                time.sleep(2)
            except Exception as e:
                if self.verbose:print("[!] Exception: "+e.message)
                reportException(e)
    
    def subredditCommentParsing(self,subredditName,sleepTime=2):
        '''
        Just reads and parses comments for subreddit, does not autoreply
        '''
        if self.verbose:print("[*] Starting comment parsing")
        while self.running:
            try:
                subreddit = self.r.get_subreddit(subredditName)
                subredditComments = subreddit.get_comments(limit=None)
                self.commentLoop(subredditComments,addTODO=True)
                time.sleep(sleepTime)
            except Exception as e:
                if self.verbose:print("[!] Exception: "+e.message)
                reportException(e)
                
    def allCommentParsing(self,sleepTime=2):
        '''
        Just reads and parses comments for all subreddits, does not autoreply
        '''
        if self.verbose:print("[*] Starting comment parsing")
        while self.running:
            try:
                all_comments = self.r.get_comments("all",limit=None)
                self.commentLoop(all_comments,addTODO=True)
                time.sleep(sleepTime)
            except Exception as e:
                if self.verbose:print("[!] Exception: "+e.message)
                reportException(e)
    
    def replyManager(self,sleepTime=10):
        '''
        Just replies to TODOs, does not read comments
        '''
        if self.verbose:print("[*] Starting reply serving")
        while self.running:
            try:
                self.manageTODOs()
                self.saveAlreadyDone()
                time.sleep(sleepTime)
            except Exception as e:
                if self.verbose:print("[!] Exception: "+e.message)
                reportException(e)
    
    def manageTODOs(self):
        while self.todo.hasNext():
            try:
                comment, replyText = self.todo.pop()
                subredditname = unicodedata.normalize('NFKD', comment.subreddit.display_name).encode('ascii','ignore')
                if self.reply:
                    comment.reply(replyText)
                    if self.verbose:print("[+] Replied to comment "+comment.id+" in /r/"+subredditname+":\n"+replyText)
                else:
                    if self.verbose:print("[+] Would reply to comment "+comment.id+" in /r/"+subredditname+":\n"+replyText)
                self.alreadyDone.add(comment.id)
                self.todoIDs.remove(comment.id)
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
    
    def commentLoop(self,comments,addTODO=False):
        for comment in comments:
            (commentisracist, quotes) = self.checkIfCommentIsRacist(comment.body.lower())
            if commentisracist and comment.author.name.lower()!=self.username.lower() and comment.id not in self.alreadyDone and comment.id not in self.todoIDs:
                replyText = "Your comment contains "
                reasonDict = {}
                totalValue = 0
                for quote in quotes:
                    key = self.racismKeyPhrases[quote] #key = (reason,value)
                    reason = key[0]
                    totalValue+=key[1]
                    if reason in reasonDict:
                        reasonDict[reason]+=1
                    else:
                        reasonDict[reason]=1
                if self.verbose:
                    subredditname = unicodedata.normalize('NFKD', comment.subreddit.display_name).encode('ascii','ignore')
                    print("[*] Found potentially racist comment: "+comment.id+" in /r/"+subredditname)
                    print("[*] Value: "+str(totalValue))
                # Make sentence based on racism
                for racismReason, count in reasonDict.iteritems():
                    replyText+=racismReason+"("+str(count)+"), "
                # Just for crackers
                print(quotes)
                if "cracker" in quotes or "crackers" in quotes:
                    replyText = replyText[:-2]+", or references to [crackers](http://en.wikipedia.org/wiki/Cracker_\(food\)), "
                
                replyText = replyText[:-2]+"!  \n\n  "
                i=1
                for quote in quotes:
                    replyText+="\t"+str(i)+". "+quote+"\n\n"
                    i+=1
                if self.verbose:
                    for racismReason, count in reasonDict.iteritems():
                        print("\t-"+racismReason)
                if self.verbose:
                    commentBody = unicodedata.normalize('NFKD', comment.body.strip()).encode('ascii','ignore')
                    print("[*] "+commentBody)
                    print("[*] Reply:\n"+replyText)
                # Try to reply
                if addTODO:
                    if self.verbose:print("[*] Adding comment to todo stack")
                    self.todo.add((comment,replyText),totalValue)
                    self.todoIDs.append(comment.id)
                else:
                    try:
                        if self.reply:
                            comment.reply(replyText)
                            if self.verbose:print("\t[+] Replied: "+replyText)
                        else:
                            if self.verbose:print("\t[+] Would reply:\n\t"+replyText)
                        self.alreadyDone.add(comment.id)
                    except praw.errors.RateLimitExceeded as e:
                        if self.verbose:
                            print("\t[!] Cannot reply: Ratelimit Error")
                            print("\t[*] "+e.message)
                            print("\t[*] Adding comment to TODO set")
                            self.todo.add((comment,replyText),totalValue)
                            self.todoIDs.append(comment.id)
                    
    def checkIfCommentIsRacist(self,commentText):
        '''
        Checks if a comment(string) is racist, returns (boolean,List)
        '''
        originalCommentText = commentText.lower()
        racistCommentList = []
        for racistComment in self.racismKeyPhrases:
            commentText = originalCommentText
            while True:
                racistLocation = commentText.find(racistComment.lower())
                if racistLocation>-1: #additional tests
                    passedTests = False
                    # If at beginning
                    if racistLocation==0:
                        # If the racist comment is at the end OR immediately followed by <space/newline>
                        if len(commentText)==racistLocation+len(racistComment):
                            passedTests = True
                        else:
                            selChar = commentText[len(racistComment)]
                            if selChar.isspace() or (selChar in string.punctuation):
                                passedTests = True
                    # Else if at end
                    elif racistLocation+len(racistComment)==len(commentText):
                        # if the char before is <space/newline>
                        selChar = commentText[racistLocation-1]
                        if selChar.isspace() or (selChar in string.punctuation):
                            passedTests = True
                    # Else in the middle
                    else:
                        selChar1 = commentText[racistLocation-1]
                        selChar2 = commentText[racistLocation+len(racistComment)]
                        if selChar1.isspace() and (selChar2.isspace() or (selChar2 in string.punctuation)):
                            passedTests = True
                    if passedTests:
                        racistCommentList.append(racistComment)
                    commentText = commentText.replace(racistComment.lower(),"",1)
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

def startThreadsAll(bot,verbose=False,multithreadReplies=False):
    t1 = Thread(target=serverHandler)
    t2 = Thread(target=networkHandler,args=(DEFAULT_NETWORK_LIMIT,bot,None,verbose))
    t3 = None
    t4 = None
    if not multithreadReplies:
        t3 = Thread(target=bot.allLoop)
    else:
        t3 = Thread(target=bot.allCommentParsing)
        t4 = Thread(target=bot.replyManager)
    try:
        t1.start()
        t2.start()
        t3.start()
        if t4:t4.start()
        t3.join()
    except Exception as e:
        bot.shutdown()
        reportException(e)
    
def startThreadsSubreddit(bot,subredditString,verbose=False,multithreadReplies=False):
    t1 = Thread(target=serverHandler)
    t2 = Thread(target=networkHandler,args=(DEFAULT_NETWORK_LIMIT,bot,None,verbose))
    t3 = None
    t4 = None
    if not multithreadReplies:
        t3 = Thread(target=bot.subredditLoop,args=(subredditString,))
    else:
        t3 = Thread(target=bot.subredditCommentParsing,args=(subredditString))
        t4 = Thread(target=bot.replyManager)
    try:
        t1.start()
        t2.start()
        t3.start()
        if t4:t4.start()
        t3.join()
    except Exception as e:
        bot.shutdown()
        reportException(e)
    
def serverHandler():
    #TODO communicate with clients
    pass

def networkHandler(limit,bot,focus=None,verbose=False):
    managing = True
    try:
        while managing:
            time.sleep(300) #Five minute TODO make changable
            netinfo = psutil.net_io_counters(pernic=True)
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
                bot.shutdown()
                managing = False
            if verbose:
                if focus in netinfo:
                    print("[*] Total network usage on "+focus+": "+str(totalusage)+"/"+str(limit))
                else:
                    print("[*] Total network usage: "+str(totalusage)+"/"+str(limit))
                    
    except Exception as e:
        if verbose:print("[!] Exception encountered, shutting down")
        bot.shutDown()
        raise e

def reportException(e,verbose=False):
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
    exceptionReportString = str(type(e))+"\n\n"+e.message
    print("[!] Crashed with exception:\n"+exceptionReportString)
    print("[!] Attempting to send message to Renmusxd")
    try:
        r.login(username,password)
        r.send_message("Renmusxd","Crash report for Antiracism_Bot","Crashed with exception:\n"+exceptionReportString)
        if verbose:print("[+] Crash report sent sucessfully")
    except Exception:
        if verbose:print("[!] Exception while sending report, sorry. There's nothing more I can do.")

if __name__ == "__main__":
    mypath = os.path.dirname(os.path.realpath(__file__))
    DEFAULT_CREDENTIAL_FILE = mypath+"/"+DEFAULT_CREDENTIAL_FILE
    DEFAULT_RACISM_FILE = mypath+"/"+DEFAULT_RACISM_FILE
    DEFAULT_RACE_FILE = mypath+"/"+DEFAULT_RACE_FILE
    DEFAULT_REPLIED_FILE = mypath+"/"+DEFAULT_REPLIED_FILE
    try:
        isverbose = False
        doesreply = True
        multithreadR = False
        if "-help" in sys.argv:
            print("Usage: python antiracism_bot.py <flags> [subreddits/all]")
            print("Flags\t\tActions")
            print("-v\t\tVerbose mode")
            print("-d\t\tNo replies")
            print("-m\t\tMultithread replies")
            print("-e\t\tExample crash report")
        else:
            if "-v" in sys.argv:
                isverbose = True
                sys.argv.remove("-v")
            if "-d" in sys.argv:
                doesreply = False
                sys.argv.remove("-d")
            if "-m" in sys.argv:
                multithreadR = True
                sys.argv.remove("-m")
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
                if isverbose:
                    print("[*] Starting threads")
                    if multithreadR:print("[*] Replying in seperate thread")
                startThreadsSubreddit(racismChecker,subredditString,verbose=isverbose,multithreadReplies=multithreadR)
            elif len(args)>1 and "all" in args:
                racismChecker = RacismChecker(username, password,DEFAULT_RACISM_FILE,DEFAULT_RACE_FILE,DEFAULT_REPLIED_FILE,verbose=isverbose,reply=doesreply)
                if isverbose:
                    print("[*] Starting threads")
                    if multithreadR:print("[*] Replying in seperate thread")
                startThreadsAll(racismChecker,verbose=isverbose,multithreadReplies=multithreadR)
            else:
                print("Type '-help' for help")
    except Exception as e:
        reportException(e)
