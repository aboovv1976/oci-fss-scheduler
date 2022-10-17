from shelve import Shelf
import oci
import datetime
import configparser
import os
from dateutil.relativedelta import relativedelta
import re
import json
import sys
import logging
import stat
import base64

def getLogger():
    logging.basicConfig(level=logging.INFO) 
    dateFormat="%Y-%m-%dT%H:%M:%S"
    format = logging.Formatter(
        fmt='%(asctime)s.%(msecs)03dZ - %(name)s - %(levelname)s - %(message)s',
        datefmt= dateFormat
    )

    ll=logging.getLogger("fss-scheduler") # 
    ll.propagate = False
    ch=logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(format)
    ll.addHandler(ch)
    return ll

Log=getLogger()

def ociApi(api,args):
    try:
        r=api(**args)
    except Exception as e:
        error(f"OCI API '{api}' failed with error " + str(e).replace('\n',' '))
        return {
            "status": 999,
            "out": None
        }
    return {
        "status": r.status,
        "out": r.data
    }

def ociConfig():

    ociConfigDir=f'{os.environ["HOME"]}/.oci'
    ociConfigFile=f"{ociConfigDir}/config"
    ociIdFile=f"{ociConfigDir}/id.key"
    try:
        os.mkdir(ociConfigDir)
    except:
        pass
    try:
        config = {
            "user": os.environ["OCI_USER_ID"],
            "key_content": os.environ["OCI_KEY"],
            "fingerprint": os.environ["OCI_KEY_DIGEST"],
            "tenancy": os.environ["OCI_TENANCY_ID"],
            "region": os.environ["OCI_REGION"],
            "compartment-id": os.environ["OCI_COMPARTMENT_ID"]
        }
    except Exception as e:
        info(f"Creating OCI config file from environment variables failed, error:" +  str(e).replace('\n',' ') + " Using default config file")
        config=oci.config.from_file()
        return config

    oci.config.validate_config(config)

    with open(ociIdFile, 'w') as idFile:
        idFile.write(base64.b64decode(config["key_content"]).decode("utf-8"))
    os.chmod(ociIdFile,stat.S_IREAD|stat.S_IWRITE)

    newConfig=config.copy()
    newConfig["key_file"]=ociIdFile
    del newConfig["key_content"]
    cfg=configparser.ConfigParser()
    cfg['DEFAULT']=newConfig
    with open(ociConfigFile, 'w') as configfile:
        cfg.write(configfile)
    os.chmod(ociIdFile,stat.S_IREAD|stat.S_IWRITE)
    return newConfig

def info(m):
    Log.info(m)

def error(m):
    Log.error(m)

def critical(m):
    Log.critical(m)

config = ociConfig()
FSSClient = oci.file_storage.FileStorageClient(config)

def timeDelta(delta):
    td=relativedelta()
    for d in delta.split(","):
        d=d.strip()
        t=re.findall('(\d+)([a-zA-Z])',d)
        if t:
            try:
                n=int(t[0][0])
            except:
                error(f"Non-numeric in the time fields in '{delta}'")
                return None
            c=t[0][1].lower()
            if c == 'h':
                td += relativedelta(hours=n)
            if c == 'd':
                td += relativedelta(days=n)
            if c == 'm':
                td += relativedelta(months=n)
            if c == 'y':
                td += relativedelta(years=n)
            if c == 'c':
                td += relativedelta(years=100*n)
        else:
            error(f"Incorrect time field in '{delta}'")
            return None
    return td      

def scheduleDetails(schedule):
    if len(schedule) != 2:
        error(f"Invalid scheduling entry '{schedule}'")
        return None
    p=schedule[0].strip()
    if re.findall('[^\w\-]',schedule[0]):
        error(f"Invalid characters in  snapshot name '{schedule[0]}'")
        return None
    name=p + "_" + datetime.datetime.strftime(datetime.datetime.utcnow(),DatePattern) 
    try:
        pDelta,nDelta=schedule[1].split(":")
    except:
        error(f"Invalid schedule '{schedule[1]}'")
        return None
    pd=timeDelta(pDelta)
    nd=timeDelta(nDelta)
    if pd and nd:
        pTime=datetime.datetime.utcnow() - pd
        nTime=datetime.datetime.utcnow() + nd
        return(
            {
                "name": name,
                "pName": p,
                "ctime": datetime.datetime.now(),
                "pTime": pTime,
                "nTime": nTime
            }
        )
    return None

def allSchedulerSnapShots(ocid):
    global Snapshots
    items=[]
    r=ociApi(
        FSSClient.list_snapshots,
        args={
            'file_system_id': ocid,
            'lifecycle_state': "ACTIVE"
            }
    )
    if r["status"] != 200:
        critical(f"FS: {FileSystems[ocid]}, OCI API list snapshot failed with status code {r['status']}")
        sys.exit(1)

    for i in r["out"]:
        try:
            expiry=datetime.datetime.strptime(i.freeform_tags["scheduled_expiry_time"],DatePattern)
        except:
            continue
        items.append(
            {
                "ocid": i.id,
                "name": i.name,
                "created": i.time_created.replace(tzinfo=None),
                "expiry": expiry
            }
        )
    Snapshots[ocid]=items

# The create API can take varying times to complete creating a jitter situation when comparing times. 
# So, allow 0.1 jitter%
def around(t):
    return t + t * 0.01

def creationRequired(ocid,pattern, t):
    for snapshot in Snapshots[ocid]:
        if snapshot["name"].lower().startswith(pattern + "_"):
            if snapshot["created"] >=  around(t):
                return False
    return True

def deleteSnapshot(ocid,name):
    r=ociApi(
        FSSClient.delete_snapshot,
        {
            "snapshot_id": ocid
        }
    )
    if r["status"] == 204:
        info(f"Deleted Snapshot: {name}")
    else:
        error(f"Deleing snapshot {name}, ocid: {ocid} failed")

def createSnapshot(ocid,name,expiry):
    ts=datetime.datetime.strftime(expiry, DatePattern)
    details=oci.file_storage.models.CreateSnapshotDetails(
        file_system_id=ocid,
        name=name,
        freeform_tags={
            "scheduled_expiry_time": ts
        }
    )
    r = ociApi(
        FSSClient.create_snapshot,
        {
            "create_snapshot_details": details
        }
    )
    if r["status"] == 200:
        info(f"FS: {FileSystems[ocid]}, Created Snapshot: {name}")
    else:
        error(f"FS: {FileSystems[ocid]}, Snapshot creation failed for {name} for FS ocid: {ocid}")

def expiredSnapshots(ocid,pattern):
    items=[]
    if ocid not in Snapshots:
        return items

    for i in Snapshots[ocid]:
        if i["name"].lower().startswith(pattern + "_"):
            if i["expiry"] < datetime.datetime.utcnow():
                items.append(
                    {
                        "ocid": i["ocid"],
                        "name": i["name"],
                        "expiry": i["expiry"]
                    }
                )
    return items

Snapshots={}
SchedulerCfgFile=os.environ["FSS_CKPT_SHCEDULER_CFG_FILE"] if "FSS_CKPT_SHCEDULER_CFG_FILE" in os.environ else f"{os.path.dirname(os.path.abspath(sys.argv[0]))}/schedule.cfg" 
SchedulerCfg=None

try:
    cfg = os.environ["FSS_CKPT_SHCEDULER_CFG"] 
    SchedulerCfg=json.loads(cfg)
except:
    SchedulerCfg = configparser.ConfigParser()
    if not SchedulerCfg.read(SchedulerCfgFile):
        info(f"Scheduler configuration file '{SchedulerCfgFile}' couldn't be read")
        sys.exit(1)

DatePattern="%Y_%m_%d-%H_%M_%S"
FileSystems={}

for ocid in SchedulerCfg.keys():
    if ocid=='DEFAULT':
        continue
    if ocid not in FileSystems:
        out=ociApi(
            FSSClient.get_file_system,
            args = {
                "file_system_id": ocid
            }
        )
        if out["status"] != 200:
            critical(f"Failed to get FS OCID {ocid} details")
            continue
        FileSystems[ocid]=out["out"].display_name

    schedules=SchedulerCfg[ocid].items()
    allSchedulerSnapShots(ocid)
    for s in  schedules:
        details=scheduleDetails(s)
        if not details:
            continue
        for snapshot in expiredSnapshots(ocid, details["pName"]):
            info(f"FS: {FileSystems[ocid]}, Expired snapshot found for {details['pName']}: {snapshot['name']}, Expired {datetime.datetime.strftime(snapshot['expiry'],'%Y/%m/%d %H:%M:%S')}")
            deleteSnapshot(snapshot["ocid"],snapshot['name'])
        if creationRequired(ocid,details['pName'],details["pTime"]):
            info(f"FS: {FileSystems[ocid]}, Snapshot Creation required with parameters - Name:{details['name']}, Expiry: {details['nTime']}")
            createSnapshot(ocid,details['name'],details['nTime'])
