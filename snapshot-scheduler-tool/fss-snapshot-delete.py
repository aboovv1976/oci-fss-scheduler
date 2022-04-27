
import oci
import datetime
import argparse

def ociConfig():
    config=oci.config.from_file()
    return config


config = ociConfig()
file_storage_client = oci.file_storage.FileStorageClient(config)

def snapshotsOf(ocid):
    r=file_storage_client.list_snapshots(
        file_system_id=ocid
    )
    items=[]
    for i in r.data:
        m={
            "ocid": i.id,
            "name": i.name,
            "time": i.time_created
        }
        items.append(m)
    return items

def createSnapshot(ocid,name):
    details=oci.file_storage.models.CreateSnapshotDetails(
        file_system_id=ocid,
        name=name,
    )
    r = file_storage_client.create_snapshot(details)
    if r.status == 200:
        print(f"Created Snapshot: {name}, ocid: {r.data.id}")
    return r.status

def deleteSnapshot(ocid,name):
    r = file_storage_client.delete_snapshot(
        snapshot_id=ocid
        )
    if r.status == 204:
        print(f"Deleted Snapshot: {name}")
    return r.status

def snapshotExists(ocid,name):
    l=snapshotsOf(ocid)
    for i in l:
        if i["name"] == name :
            return True
    return False

def getSnapshot(ocid,name):
    l=snapshotsOf(ocid)
    for i in l:
        if i["name"] == name :
            return i["ocid"]
    return None

def olderSnapshots(ocid,n,delete=False): #OCID and seconds
#Deletes snapshots older than 'n' number of seconds
    snapshots=[]
    for i in snapshotsOf(ocid):
        p =  i["time"] - datetime.timedelta(seconds=n)
        now=datetime.datetime.now().timestamp()
        if i["time"].timestamp() < (now - n):
            snapshots.append(i)
    return snapshots

DELETE=False

parser = argparse.ArgumentParser()
parser.add_argument('--file-system-id', type=str, required=True)
parser.add_argument('--seconds', type=int, required=False)
parser.add_argument('--hours', type=int, required=False)
parser.add_argument('--days', type=int, required=False)
parser.add_argument('--minutes', type=int, required=False)
parser.add_argument('--delete', action='store_true')
args = parser.parse_args()
s=0
ocid=args.file_system_id
if (args.days):
    s+=args.days*24*3600
if (args.hours):
    s+=args.hours*3600
if (args.minutes):
    s+=args.minutes*60
if (args.seconds):
    s+=args.seconds
if (args.delete):
    DELETE=True

s=olderSnapshots(ocid,s)
for i in s:
    
    if DELETE:
        print(f"Deleting Name: {i['name']}", f"Time: {i['time'].strftime('%m/%d/%Y, %H:%M:%S')}")
        deleteSnapshot(i['ocid'], i['name'] )
    else:
        print(f"Name: {i['name']}", f"Time: {i['time'].strftime('%m/%d/%Y, %H:%M:%S')}")