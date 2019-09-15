import sqlite3
import tkinter
from tkinter import filedialog
from tkinter import *
from tkinter.messagebox import showerror
import shutil
import sys



############################## CONSTANTS ##############################
DEBUG = 1
PARENT_GROUP_TITLE = 'AUTO'
SUBARRAY_GROUP_TITLE = 'SUBarray LR'
VIEWS_REMOVE_TEXT = 'Remove all views and groups? (y/n)'
INPUT_GROUP_TEXT = 'Create input groups? (y/n)'
SUBARRAY_GROUP_TEXT = 'Create SUBarray LR group? (y/n)'
FALLBACK_TEXT = 'Create fallback controls? (y/n)'
DS_TEXT = 'Create DS info? (y/n)'
METERS_TEXT = 'Create meters view? (y/n)'
METERS_REMOVE_TEXT = 'Remove meters view? (y/n)'
INPUT_SNAPSHOT = "Inputs"
INPUT_TYPES = ["A1", "A2", "A3", "A4", "D1", "D2", "D3", "D4"]
ARRAYCALC_SNAPSHOT = 1
TEMPLATE_NAMES = ['Fallback', 'Fallback LR', 'Fallback Overview', 'Mute', 'DS Status', 'Meter', 'Meters Group', 'Meter NODS']
METER_WINDOW_TITLE = "AUTO - Meters"
METER_VIEW_WIDTH = 2000
METER_VIEW_HEIGHT = 7000
METER_VIEW_STARTX = 15
METER_VIEW_STARTY = 15
METER_GROUP_SPACING = 230
METER_SPACING_X = 15
METER_SPACING_Y = 15
FB_OVERVIEW_POSX = 842
FB_OVERVIEW_POSY = 16
DS_STATUS_STARTX = FB_OVERVIEW_POSX
DS_STATUS_STARTY = 400
#LR group mute buttons
LR_MUTE_TEXT = ['Left', 'Right']
LR_MUTE_POSX = [700, 770]
LR_MUTE_POSY = 56
LR_FB_POSX = 485
LR_FB_POSY = 227
#SUBarray LR group mute buttons
SUBLR_MUTE_TEXT = ['Left', 'Right']
SUBLR_MUTE_POSX = [96, 166]
SUBLR_MUTE_POSY = 230
SUBLR_FB_POSX = 382
SUBLR_FB_POSY = 16

GROUPID = 0
SUBGROUP = 0
TARGET_CHANNEL = 4
TARGET_ID = 3


ctrlStr = 'INSERT INTO "main"."Controls" ("Type", "PosX", "PosY", "Width", "Height", "ViewId", "DisplayName", "JoinedId", "LimitMin", "LimitMax", "MainColor", "SubColor", "LabelColor", "LabelFont", "LabelAlignment", "LineThickness", "ThresholdValue", "Flags", "ActionType", "TargetType", "TargetId", "TargetChannel", "TargetProperty", "TargetRecord", "ConfirmOnMsg", "ConfirmOffMsg", "PictureIdDay", "PictureIdNight", "Font", "Alignment", "Dimension") '

##########################################################################################



############################## GLOBALS ##############################
views = []
filename = "r1.dbpr"
glDS = 1
glParentId = 1
glJoinedId = 1
##########################################################################################



####################### CLASSES  ##############################
class Channel:
    def __init__(self, targetId, targetChannel):
        self.targetId = targetId
        self.targetChannel = targetChannel
        self.inputEnable = []
        self.name = "name"

    def print(self):
        dprint(f'CHANNEL: id - {self.targetId} / channel - {self.targetChannel} / name - {self.name}')
        dprint(self.inputEnable)

class Group:
    def __init__(self, groupId, name):
        self.groupId = groupId
        self.name = name
        self.viewId = None
        self.groupIdSt = []
        self.targetDevices = []

    def print(self):
        dprint(f'GROUP: {self.name} / {self.groupId} / Subgroups: {len(self.groupIdSt)}')
        for g in self.groupIdSt:
            dprint(g.name)
        for d in self.targetChannels:
            dprint(d)

    @property
    def viewId(self):
        return self._viewId

    @viewId.setter
    def viewId(self, value):
        self._viewId = value

class Template:
    def __init__(self, name):
        self.name = name
        self.joinedId = 0
        self.contents = []

    def print(self):
        dprint(f'{self.name} - JoinedId: {self.joinedId} - Contents Length: {len(self.contents)}')


##########################################################################################





############################## METHODS ##############################

def getTempContents(tempArray, tempName):
    for t in tempArray:
        if t.name == tempName:
            return t.contents
    return -1;

def findDevicesInGroups(parentId):
    proj_c.execute(f'SELECT * FROM "main"."Groups" WHERE ParentId = {parentId}')
    rtn = proj_c.fetchall()
    ch = []
    for row in rtn:
        if row[TARGET_ID] == SUBGROUP: # If entry is not a device but a subgroup
            ch += findDevicesInGroups(row[GROUPID])
        else:
            return rtn

    return ch

def insertTemplate(temps, tempName, posX, posY, viewId, displayName, targetId, targetChannel, proj_c, width, height, joinedId, targetProp, targetRec):
    dprint(f'TEMPLATE: {tempName} / {posX} / {posY} / {viewId} / {displayName} / {targetId} / {targetChannel} / {width} / {height} / {joinedId} / {targetProp} / {targetRec}')
    frameW = 0
    frameH = 0

    global glJoinedId
    if joinedId is not None:
        jId = joinedId
    else:
        jId = glJoinedId
        glJoinedId = glJoinedId + 1

    for row in getTempContents(temps, tempName):
        tProp = targetProp
        tRec = targetRec
        tChannel = targetChannel
        tId = targetId
        w = width

        if tId is None:
            tId = row[22]

        if tChannel is None:
            tChannel = row[23]

        if w is None:
            w = row[4]

        h = row[5]
        if height is not None:
            if height > 0:
                h = height
        dName = row[7]
        if row[1] == 12: # If item is a Frame
            frameW = w
            frameH = h
            if (displayName is not None):
                dName = displayName
        if dName == None:
            dName = ""

        if tProp == None:
            tProp = row[24]
        if tRec == None:
            tRec = row[25]

        if (tProp == "Input_Digital_TxStream") or (tProp == "Input_Digital_DsDataPri") or (tProp == "Input_Digital_DsDataSec") or (tProp == "Input_Digital_Sync"):
            if tChannel > -1:
                tChannel = 0 #Dante + digital info require channel ID to be 0

        if tProp is not None:
            if len(tProp) > 1:
                dprint(f'tProp - {tProp} / tRec - {tRec} / tId - {tId} / tChannel - {tChannel}')

        proj_c.execute(f'INSERT INTO "main"."Controls" ("Type", "PosX", "PosY", "Width", "Height", "ViewId", "DisplayName", "JoinedId", "LimitMin", "LimitMax", "MainColor", "SubColor", "LabelColor", "LabelFont", "LabelAlignment", "LineThickness", "ThresholdValue", "Flags", "ActionType", "TargetType", "TargetId", "TargetChannel", "TargetProperty", "TargetRecord", "ConfirmOnMsg", "ConfirmOffMsg", "PictureIdDay", "PictureIdNight", "Font", "Alignment", "Dimension") VALUES ("{str(row[1])}", "{str(row[2]+posX)}", "{str(row[3]+posY)}", "{str(w)}", "{str(h)}", "{str(viewId)}", "{dName}", "{str(jId)}", "{str(row[10])}", "{str(row[11])}", "{str(row[12])}", "{str(row[13])}", "{str(row[14])}", "{str(row[15])}", "{str(row[16])}", "{str(row[17])}", "{str(row[18])}", "{str(row[19])}", "{str(row[20])}", "{str(row[21])}", "{str(tId)}", {str(tChannel)}, "{str(tProp)}", {tRec}, NULL, NULL, "{str(row[28])}", "{str(row[29])}", "{str(row[30])}", "{str(row[31])}", " ")')
    return [frameW, frameH]

def dprint(s):
    if DEBUG > 0:
        print(s)

##########################################################################################









# SQL Setup
dbTemplate = sqlite3.connect('templates.r2t')
dbProj = sqlite3.connect(filename)
template_c = dbTemplate.cursor()
proj_c = dbProj.cursor()

#root = Tk()
#root.filename =  filedialog.askopenfilename(initialdir = "/Desktop",title = "Select project file",filetypes = (("d&b files","*.dbpr"),("all files","*.*")))
#print (root.filename)

##### LOAD TEMPLATES
temps = []
template_c.execute('SELECT * FROM "main"."Sections" ORDER BY JoinedId ASC')
rtn  = template_c.fetchall()
for t in TEMPLATE_NAMES:
    temps.append(Template(t))
for row in rtn:
    for i in range(len(temps)):
        if row[1] == temps[i].name:
            temps[i].joinedId = row[3]
            template_c.execute(f'SELECT * FROM "main"."Controls" WHERE JoinedId = {temps[i].joinedId}')
            temps[i].contents = template_c.fetchall()

# Set joinedId start
proj_c.execute('SELECT JoinedId from "main"."Controls" ORDER BY JoinedId DESC LIMIT 1')
try:
    glJoinedId = proj_c.fetchone()[0] + 1
    dprint(f'glJoined - {glJoinedId}')
except:
    print("Views have not been generated. Please run initial setup in R1 first.")
    sys.exit();


userIp = " "
while (userIp != "y") and (userIp != "n") and (userIp != ""):
    userIp = input(VIEWS_REMOVE_TEXT)

if (userIp == "y"):
    proj_c.execute(f'SELECT ViewId FROM "main"."Views" WHERE Type = 1000')
    rtn = proj_c.fetchall()
    for row in rtn:
        proj_c.execute(f'DELETE FROM "main"."Controls" WHERE ViewId = {row[0]};')
        proj_c.execute(f'DELETE FROM "main"."Views" WHERE ViewId = {row[0]};')
    proj_c.execute(f'DELETE FROM "main"."Groups" WHERE NOT GroupId = 1')

    dbTemplate.close()
    dbProj.commit()
    dbProj.close()
    sys.exit()


##################### Create input groups #####################
userIp = " "
while (userIp != "y") and (userIp != "n") and (userIp != ""):
    userIp = input(INPUT_GROUP_TEXT)

ipGroupId = [0,0,0,0,0,0,0,0]
if (userIp == "y") or (userIp == ""):

    #Create channel list
    #proj_c.execute(f'SELECT * FROM "main"."Snapshots" ORDER BY SnapshotId ASC')
    #rtn = proj_c.fetchall()
    #i = 1
    #for row in rtn:
    #    print(f'[{i}] - {row[2]}')
    #    i += 1;
    #userIp = input('Select snapshot to retrieve input patch from (default 1):')
    #if userIp == "":
    #    userIp = ARRAYCALC_SNAPSHOT
    #dprint('Snapshot chosen:')
    #dprint(rtn[int(userIp)-1])
    #snapId = rtn[int(userIp)-1][0]

    #Load all channels. Pass ' TargetProperty = "Config_InputEnable1"' in the SQL request to retrieve every channel once in the query
    channels = []
    proj_c.execute(f'SELECT TargetId, TargetNode FROM "main"."SnapshotValues" WHERE SnapshotId = {ARRAYCALC_SNAPSHOT} AND TargetProperty = "Config_InputEnable1" ORDER BY TargetId ASC')
    rtn = proj_c.fetchall()
    for row in rtn:
        channels.append(Channel(row[0], row[1]))
    for i in range(len(channels)): # Find name for all channels
        proj_c.execute(f'SELECT Name FROM "main"."AmplifierChannels" WHERE DeviceId = {channels[i].targetId} AND AmplifierChannel = {channels[i].targetChannel}')
        channels[i].name = proj_c.fetchone()[0]


    #Find ip routing for each channel
    ipStr = ["Config_InputEnable1", "Config_InputEnable2", "Config_InputEnable3", "Config_InputEnable4", "Config_InputEnable5", "Config_InputEnable6", "Config_InputEnable7", "Config_InputEnable8"]
    for c in channels:
        for s in ipStr:
            proj_c.execute(f'SELECT * FROM "main"."SnapshotValues" WHERE SnapshotId = {ARRAYCALC_SNAPSHOT} AND TargetId = {c.targetId} AND TargetNode = {c.targetChannel} AND TargetProperty = "{s}" AND Value = 1 ORDER BY TargetId')
            rtn = proj_c.fetchall()
            c.inputEnable.append(len(rtn));

    ## Create 'Auto' group
    # Create group if it does not already exist
    proj_c.execute(f'SELECT GroupId FROM "main"."Groups" WHERE Name = "{PARENT_GROUP_TITLE}"')
    try:
        glParentId = proj_c.fetchone()[0]
    except:
        proj_c.execute(f'INSERT INTO "main"."Groups"("Name","ParentId","TargetId","TargetChannel","Type","Flags") VALUES ("{PARENT_GROUP_TITLE}",1,0,-1,0,0);')
        proj_c.execute(f'SELECT GroupId FROM "main"."Groups" WHERE Name = "{PARENT_GROUP_TITLE}"')
        glParentId = proj_c.fetchone()[0]


    ## Create groups
    #Delete groups if already existing
    ipGroupId = []
    for s in INPUT_TYPES:
        proj_c.execute(f'SELECT GroupId FROM "main"."Groups" WHERE Name = "{s}" AND ParentId = {glParentId}')
        try:
            rtn = proj_c.fetchone()
            dprint(f'Deleting existing input group: {s} - {rtn[0]}')
            proj_c.execute(f'DELETE FROM "main"."Groups" WHERE GroupId = {rtn[0]}')
            proj_c.execute(f'DELETE FROM "main"."Groups" WHERE ParentId = {rtn[0]}')
        except:
            dprint(f'No existing input group found for {s} {glParentId}')

        proj_c.execute(f'INSERT INTO "main"."Groups"("Name","ParentId","TargetId","TargetChannel","Type","Flags") VALUES ("{s}",{glParentId},0,-1,0,0);')
        proj_c.execute(f'SELECT GroupId FROM "main"."Groups" WHERE Name = "{s}"')
        ipGroupId.append(proj_c.fetchone()[0])

    for c in channels:
        for i in range(len(c.inputEnable)):
            if c.inputEnable[i] > 0:
                proj_c.execute(f'INSERT INTO "main"."Groups"("Name","ParentId","TargetId","TargetChannel","Type","Flags") VALUES ("{c.name}",{ipGroupId[i]},{c.targetId},{c.targetChannel},1,0);')

###############################################################


## Populate groups
# Auto-Find Group ids and names
proj_c.execute('SELECT "GroupId" FROM "main"."Groups" ORDER BY "GroupId" ASC LIMIT 3')
priGrpId = proj_c.fetchall()[1][0]
groups = []
rtn = proj_c.execute(f'SELECT * FROM "main"."Groups" WHERE "ParentId" = {priGrpId}')
for row in rtn:
    groups.append(Group(row[0], row[1])) #First is GroupId, second is Name

for i in range(len(groups)): # Determine stereo (Main L/R) and mono groups + get view ids
    g = groups[i]

    groups[i].targetChannels = findDevicesInGroups(g.groupId)

    proj_c.execute(f'SELECT "ViewId" FROM "main"."Views" WHERE Name = "{groups[i].name}" ORDER BY ViewId ASC LIMIT 1;') # Get view IDs
    rtn = proj_c.fetchone()
    try:
        groups[i].viewId = rtn[0]
    except:
        dprint(f"Could not find view for {groups[i].name} group.")

    # Find any L/R or SUB L/R subgroups
    for g in [" TOPs L", " TOPs R", " SUBs L", " SUBs R"]:
        proj_c.execute(f'SELECT * FROM "main"."Groups" WHERE "Name" = "{groups[i].name + g}"')
        try:
            rtn = proj_c.fetchone()
            groups[i].groupIdSt.append(Group(rtn[0], rtn[1]))
            groups[i].groupIdSt[-1].targetChannels = findDevicesInGroups(groups[i].groupIdSt[-1].groupId)
        except:
            asdasd = 1;
            #dprint(f"No {g} group found for {groups[i].name} group.")

    if groups[i].name == "SUBarray": # Create LR groups for SUBarray
        userIp = " "
        while (userIp != "y") and (userIp != "n") and (userIp != ""):
            userIp = input(SUBARRAY_GROUP_TEXT)

        if (userIp == "y") or (userIp == ""):
            groupL = []
            groupR = []
            for tc in groups[i].targetChannels:
                if " L" in tc[1]:
                    groupL.append(tc)
                else:
                    groupR.append(tc)

            ## Create SUBarray LR group
            # If group already exists, delete and then recreate with new device list
            proj_c.execute(f'SELECT GroupId FROM "main"."Groups" WHERE Name = "{SUBARRAY_GROUP_TITLE}" AND ParentId = "{glParentId}"')
            try:
                pId = proj_c.fetchone()[0]

                proj_c.execute(f'SELECT GroupId FROM "main"."Groups" WHERE ParentId = "{pId}"') #Get L+R groups
                rtn = proj_c.fetchall()
                dprint(f'Deleting existing SUBarray groups - {pId} - {rtn[0][0]} / {rtn[1][0]}')
                proj_c.execute(f'DELETE FROM "main"."Groups" WHERE GroupId = {pId};')
                for row in rtn:
                    proj_c.execute(f'DELETE FROM "main"."Groups" WHERE ParentId = {row[0]};')
                    proj_c.execute(f'DELETE FROM "main"."Groups" WHERE GroupId = {row[0]};')
            except:
                dprint('No existing SUBarray groups found.')

            proj_c.execute(f'INSERT INTO "main"."Groups"("Name","ParentId","TargetId","TargetChannel","Type","Flags") VALUES ("{SUBARRAY_GROUP_TITLE}",{glParentId},0,-1,0,0);')
            proj_c.execute(f'SELECT GroupId FROM "main"."Groups" WHERE Name = "{SUBARRAY_GROUP_TITLE}"')
            pId = proj_c.fetchone()[0]

            gStr = ["SUBarray L", "SUBarray R"]
            g = groupL
            for s in gStr:
                proj_c.execute(f'INSERT INTO "main"."Groups"("Name","ParentId","TargetId","TargetChannel","Type","Flags") VALUES ("{s}",{pId},0,-1,0,0);')
                proj_c.execute(f'SELECT * FROM "main"."Groups" WHERE "Name" = "{s}"')
                rtn = proj_c.fetchone()

                for tc in g:
                    proj_c.execute(f'INSERT INTO "main"."Groups"("Name","ParentId","TargetId","TargetChannel","Type","Flags") VALUES ("{tc[1]}",{rtn[0]},{tc[3]},{tc[4]},1,0);')

                groups[i].groupIdSt.append(Group(rtn[0], rtn[1]))
                groups[i].groupIdSt[-1].targetChannels = findDevicesInGroups(groups[i].groupIdSt[-1].groupId)

                g = groupR


##################### FALLBACK CONTROLS #####################

userIp = " "
while (userIp != "y") and (userIp != "n") and (userIp != ""):
    userIp = input(FALLBACK_TEXT)

if (userIp == "y") or (userIp == ""):
    # Find Overview viewId + add master fallback frame
    proj_c.execute(f'SELECT "ViewId" FROM "main"."Views" WHERE Name = "Overview";') # Get view IDs
    overviewId = 0
    try:
        overviewId = proj_c.fetchone()[0]
    except:
        print("Views have not been generated. Please run initial setup in R1 first.")
        sys.exit();

    proj_c.execute(f'SELECT "GroupId" FROM "main"."Groups" WHERE ParentId = "1" AND Name = "Master";') # Get view IDs
    masterId = proj_c.fetchone()[0]

    proj_c.execute(f'UPDATE "main"."Views" SET HRes = {1200} WHERE ViewId = {overviewId}')

    userIp = " "
    while (userIp != "y") and (userIp != "n") and (userIp != ""):
        userIp = input(DS_TEXT)


    if (userIp == "y") or (userIp == ""):
        posX = DS_STATUS_STARTX
        posY = DS_STATUS_STARTY
        for i in range(len(INPUT_TYPES[6:])):
            dprint(f'i - {i} / INPUT_TYPES[4+i] - {INPUT_TYPES[4+i]} / ipGroupId[4+i] - {ipGroupId[4+i]} /')
            w = insertTemplate(temps, "DS Status", posX, posY, overviewId, INPUT_TYPES[4+i], ipGroupId[4+i], -1, proj_c, None, None, None, None, i+1);
            posX += w[0]
    else:
        glDS = 0

    insertTemplate(temps, "Fallback Overview", FB_OVERVIEW_POSX, FB_OVERVIEW_POSY, overviewId, None, masterId, None, proj_c, None, None, None, None, None);




    for i in range(len(groups)): # Determine stereo (Main L/R) and mono groups + get view ids
        # Delete input routing and clock selection views
        dsplyNames = ["Input Routing"]#, "Digital Input Clock", "Digital Input Clock Left", "Digital Input Clock Right"]
        for d in dsplyNames:
            proj_c.execute(f'SELECT "JoinedId" FROM "main"."Controls" WHERE DisplayName = "{d}" AND ViewId = "{groups[i].viewId}"')
            try:
                for row in proj_c.fetchall():
                    proj_c.execute(f'DELETE FROM "main"."Controls" WHERE JoinedId = {row[0]};')
            except:
                dprint(f"Could not find {d} info for {groups[i].name}")


        fbX = 0
        fbY = 0
        if (len(groups[i].groupIdSt) > 0): #LR group
            template = "Fallback LR"

            if(groups[i].name.find("SUB") > -1) and (groups[i].name.find("array") > -1):#SUBarray group
                fbX = SUBLR_FB_POSX
                fbY = SUBLR_FB_POSY
                muteX = SUBLR_MUTE_POSX
                muteY = SUBLR_MUTE_POSY
                muteText = SUBLR_MUTE_TEXT

            else:
                fbX = LR_FB_POSX
                fbY = LR_FB_POSY
                muteX = LR_MUTE_POSX
                muteY = LR_MUTE_POSY
                muteText = LR_MUTE_TEXT

            for j in range(len(muteText)):
                insertTemplate(temps, 'Mute', muteX[j], muteY, groups[i].viewId, muteText[j], groups[i].groupIdSt[j].groupId, None, proj_c, None, None, None, None, None);
        else:
            template = "Fallback" #Point sources
            fbX = 307
            fbY = 228


        insertTemplate(temps, template, fbX, fbY, groups[i].viewId, None, groups[i].groupId, None, proj_c, None, None, None, None, None);

#####################  #####################


proj_c.execute(f'SELECT * FROM "main"."Views" WHERE Name = "{METER_WINDOW_TITLE}"')
if proj_c.fetchone() is not None:
    dprint(f'Found existing {METER_WINDOW_TITLE} view.')
    userIp = " "
    while (userIp != "y") and (userIp != "n") and (userIp != ""):
        userIp = input(METERS_REMOVE_TEXT)

    if (userIp == "y"):
        dprint(f'Deleting existing {METER_WINDOW_TITLE} view.')
        proj_c.execute(f'SELECT ViewId FROM "main"."Views" WHERE Name = "{METER_WINDOW_TITLE}"')
        meterViewId = proj_c.fetchone()[0]
        proj_c.execute(f'DELETE FROM "main"."Controls" WHERE ViewId = {meterViewId};')
        proj_c.execute(f'DELETE FROM "main"."Views" WHERE ViewId = {meterViewId};')





##################### METER VIEW #####################
userIp = " "
while (userIp != "y") and (userIp != "n") and (userIp != ""):
    userIp = input(METERS_TEXT)

if (userIp == "y") or (userIp == ""):
    proj_c.execute(f'INSERT INTO "main"."Views"("Type","Name","Icon","Flags","HomeViewIndex","NaviBarIndex","HRes","VRes","ZoomLevel","ScalingFactor","ScalingPosX","ScalingPosY","ReferenceVenueObjectId") VALUES (1000,"{METER_WINDOW_TITLE}",NULL,4,NULL,-1,{METER_VIEW_WIDTH},{METER_VIEW_HEIGHT},100,NULL,NULL,NULL,NULL);')
    proj_c.execute(f'SELECT ViewId FROM "main"."Views" WHERE Name = "{METER_WINDOW_TITLE}"')
    meterViewId = proj_c.fetchone()[0]

    posX = METER_VIEW_STARTX
    posY = METER_VIEW_STARTY

    if glDS == 0:
        template_c.execute(f'SELECT Width, Height FROM "main"."Controls" WHERE DisplayName = "METERS_TITLE_NODS"')
    else:
        template_c.execute(f'SELECT Width, Height FROM "main"."Controls" WHERE DisplayName = "METERS_TITLE"')
    rtn = template_c.fetchone()
    dprint(rtn)
    meterW = rtn[0]
    meterH = rtn[1]
    spacingX = meterW+METER_SPACING_X
    spacingY = meterH+METER_SPACING_Y


    groups2 = []
    for g in groups:
        if len(g.groupIdSt) < 1:
            groups2.append(g)
        else:
            for sg in g.groupIdSt:
                groups2.append(sg)

    for g in groups2:

        insertTemplate(temps, 'Meters Group', posX, posY, meterViewId, g.name, None, None, proj_c, meterW, None, None, None, None);

        posY = 40

        jId = glJoinedId
        for d in g.targetChannels:
            if glDS == 0:
                s = "Meter NODS"
            else:
                s = "Meter"

            insertTemplate(temps, s, posX, posY, meterViewId, d[1], d[3], d[4], proj_c, None, None, jId, None, None);

            posY += spacingY
        posX += spacingX
        posY = METER_VIEW_STARTY
        glJoinedId = glJoinedId + 1
#####################  #####################

dbTemplate.commit()
dbTemplate.close()
dbProj.commit()
dbProj.close()
sys.exit()
