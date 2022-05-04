

This repository provides a few techniques to manage OCI FSS snapshots. Deletion of snapshots based on age and automatically scheduling the creation and deletion of snapshots.  The files are in ***snapshot-scheduler-tool*** folder. 

***1) OCI FSS Snapshot delete***  
***2) OCI FSS Snapshot Scheduler***

Note: The provided aboovv/fss-snapshot-scheduler image is a generic OCI CLI/API python container that can be used with any API/CLI requirements. 

# OCI FSS Snapshot delete

The repository provides fss-snapshot-delete.py as a standalone script to delete snapshots based on its age. This is a seperate script to the snapshot scheduler. 

## Usage
```
$ python ./fss-snapshot-delete.py 
usage: fss-snapshot-delete.py [-h] --file-system-id FILE_SYSTEM_ID
                              [--seconds SECONDS] [--hours HOURS]
                              [--days DAYS] [--minutes MINUTES] [--delete]
fss-snapshot-delete.py: error: the following arguments are required: --file-system-id
$
```
#### List all snapshots

```
$ python ./fss-snapshot-delete.py  --file-system-id ocid1.filesystem.oc1.iad.aaaaaaaaaac2b2xbnfqwillqojxwiotjmfsc2ylefuzaaaaa 
Name: hourly_snapshot_2022_04_12-17_15_29 Time: 04/12/2022, 17:15:29
Name: daily_snapshot_2022_04_12-16_17_04 Time: 04/12/2022, 16:17:04
Name: hourly_snapshot_2022_04_12-15_41_15 Time: 04/12/2022, 15:41:15
Name: yearly_snapshot_2022_04_11-15_56_26 Time: 04/11/2022, 15:56:27
Name: monthly_snapshot_2022_04_11-15_56_25 Time: 04/11/2022, 15:56:25
Name: daily_snapshot_2022_04_11-15_56_22 Time: 04/11/2022, 15:56:24
$
```

#### List snapshots one day old

```
$ python ./fss-snapshot-delete.py  --file-system-id ocid1.filesystem.oc1.iad.aaaaaaaaaac2b2xbnfqwillqojxwiotjmfsc2ylefuzaaaaa  --days 1
Name: yearly_snapshot_2022_04_11-15_56_26 Time: 04/11/2022, 15:56:27
Name: monthly_snapshot_2022_04_11-15_56_25 Time: 04/11/2022, 15:56:25
Name: daily_snapshot_2022_04_11-15_56_22 Time: 04/11/2022, 15:56:24
```
#### Delete snapshots older than 1 day

```
$ python ./fss-snapshot-delete.py  --file-system-id ocid1.filesystem.oc1.iad.aaaaaaaaaac2b2xbnfqwillqojxwiotjmfsc2ylefuzaaaaa  --days 1 --delete
Deleting Name: yearly_snapshot_2022_04_11-15_56_26 Time: 04/11/2022, 15:56:27
Deleted Snapshot: yearly_snapshot_2022_04_11-15_56_26
Deleting Name: monthly_snapshot_2022_04_11-15_56_25 Time: 04/11/2022, 15:56:25
Deleted Snapshot: monthly_snapshot_2022_04_11-15_56_25
Deleting Name: daily_snapshot_2022_04_11-15_56_22 Time: 04/11/2022, 15:56:24
Deleted Snapshot: daily_snapshot_2022_04_11-15_56_22
[opc@kube scheduler]$
```
Use any combination of seconds, hours, minutes and days for listing and deleting. 


# OCI FSS Snapshot Scheduler

This is a script used to create and delete FSS snapshots based on a pre-defined schedule. This creates the snapshots as well as deletes the expired snapshots. 

## Usage

The scheduler can be used in three ways.

***Option 1.*** As a stand alone script - fss-scheduler.py. This can be placed in cron job to run every one hour. The script will create and delete (expire) snapshots as defined in scheduler.cfg file or using *FSS_CKPT_SHCEDULER_CFG* environment variable.

***Option 2.*** This includes a Dockerfile that can be used to build a docker image. This is based on alpine Linux and includes all the required modules including oci api. Run the docker image every hour. This is a container and has no pre-requisites such as OCI API module or other libraries. 

***Option 3.*** Run in K8s cluster with the above docker image  as cron job 

### Option 1: Standalone script

In its simplest form, just copy the fss-scheduler.py, oci_api.py and schedule.cfg and then modify the schedule.cfg with FS ocid and schedule details.  Run fss-scheduler.py (one time use) 

- The OCI API python modules should be installed. See [OCI SDK for Python](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/pythonsdk.htm). 

- install it in cron to run every hour. The user the script is installed as cron should have the OCI configuration created (or use the environment variable for OCI credentials).  [Configuring the CLI](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliconfigure.htm)

#### Sample

```
$ python ./fss-scheduler.py  
2022-04-12T15:30:16.245Z - fss-scheduler - INFO - Creating OCI config file from environment variables failed, error:'OCI_USER_ID' Using default config file  
2022-04-12T15:30:16.630Z - fss-scheduler - INFO - Expired snapshot found for hourly_snapshot: hourly_snapshot_2022_04_12-02_49_20, Expired 2022/04/12 03:49:20   
2022-04-12T15:30:17.434Z - fss-scheduler - INFO - Deleted Snapshot: hourly_snapshot_2022_04_12-02_49_20  
2022-04-12T15:30:17.434Z - fss-scheduler - INFO - Snapshot Creation required with parameters - Name:hourly_snapshot_2022_04_12-15_30_16, Expiry: 2022-04-12 16:30:16.630778  
2022-04-12T15:30:28.706Z - fss-scheduler - INFO - Created Snapshot: hourly_snapshot_2022_04_12-15_30_16  
$  
$ cat schedule.cfg  
[ocid1.filesystem.oc1.iad.aaaaaaaaaac2b2xbnfqwillqojxwiotjmfsc2ylefuzaaaaa] # FSName: Rclone-fs  
Hourly_Snapshot = 1h:1h  
Daily_Snapshot =  1d:1m  
Monthly_SnapShot = 1m:1y  
Yearly_Snapshot =  1y:1c  
$ 
$ crontab -l
0 * * * *  python /home/opc/scheduler/fss-scheduler.py
$ 

```

### Option 2: docker

The advantage of using docker image is that it comes with all the modules installed and should not have any other dependancies. 

> sudo docker run -it --env-file env aboovv/fss-snapshot-scheduler

This will run just once but requires the above to be installed as a cronjob. The env file should be populated as mentioned in the next section. That is *FSS_CKPT_SHCEDULER_CFG* and OCI authentication environment variables. 

#### Sample
```
$ sudo docker run -it --env-file env aboovv/fss-snapshot-scheduler
2022-04-12T15:41:15.601Z - fss-scheduler - INFO - Snapshot Creation required with parameters - Name:hourly_snapshot_2022_04_12-15_41_15, Expiry: 2022-04-13 15:41:15.601073  
2022-04-12T15:41:18.354Z - fss-scheduler - INFO - Created Snapshot: hourly_snapshot_2022_04_12-15_41_15  
2022-04-12T15:41:18.424Z - fss-scheduler - INFO - Snapshot Creation required with parameters - Name:monthly_snapshot_2022_04_12-15_41_18, Expiry: 2024-04-12 15:41:18.424715  
2022-04-12T15:41:28.678Z - fss-scheduler - INFO - Created Snapshot: monthly_snapshot_2022_04_12-15_41_18  
2022-04-12T15:41:28.679Z - fss-scheduler - INFO - Snapshot Creation required with parameters - Name:yearly_snapshot_2022_04_12-15_41_28, Expiry: 2122-04-12 15:41:28.678960  
2022-04-12T15:41:30.713Z - fss-scheduler - INFO - Created Snapshot: yearly_snapshot_2022_04_12-15_41_28  
$ sudo docker run -it --env-file env aboovv/fss-snapshot-scheduler 
$ cat env  
OCI_USER_ID=ocid1.user.oc1..<removed>  
OCI_TENANCY_ID=ocid1.tenancy.oc1..<removed>  
OCI_KEY_DIGEST=a3:49:..<removed>  
OCI_REGION=us-ashburn-1  
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..<removed>  
FSS_CKPT_SHCEDULER_CFG={"ocid1.filesystem.oc1.iad.aaaaaaaaaac2b2xbnfqwillqojxwiotjmfsc2ylefuzaaaaa": {"hourly_snapshot": "1h:1d", "daily_snapshot": "1d:1m", "monthly_snapshot": "1m:6m"}, "ocid1.filesystem.oc1.iad.aaaaaaaaaaczrj4infqwillqojxwiotjmfsc2ylefuzaaaaa": {"monthly_snapshot": "1m:2y", "yearly_snapshot": "1y:1c"}}  
OCI_KEY=LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVkt...<removed - generated using echo "OCI_KEY=`cat ~/.oci/private_key.pem | base64 -w 0`" >> env>  
```

  
### Option 3: Kubernetes

> kubectl apply -f k8s-cron.yaml

The environment variables should be updated in the k8s-cron.yaml file. See the next sections for the required environment variable. That is *FSS_CKPT_SHCEDULER_CFG* and OCI authentication environment variables. 

#### Sample

```
# kubectl apply -f k8s-cron.yaml
```
(If you happened to catch the pod running. See the logs)
```
# kubectl logs fss-scheduler-27496334-vcbwl 
2022-04-12T16:17:04.270Z - fss-scheduler - INFO - Snapshot Creation required with parameters - Name:daily_snapshot_2022_04_12-16_17_04, Expiry: 2022-05-12 16:17:04.270005
2022-04-12T16:17:04.270Z - fss-scheduler - INFO - Snapshot Creation required with parameters - Name:daily_snapshot_2022_04_12-16_17_04, Expiry: 2022-05-12 16:17:04.270005
2022-04-12T16:17:06.794Z - fss-scheduler - INFO - Created Snapshot: daily_snapshot_2022_04_12-16_17_04

$ cat k8s-cron.yaml 
apiVersion: batch/v1
kind: CronJob
metadata:
  name: fss-scheduler
spec:
  schedule: "0 * * * *"
  successfulJobsHistoryLimit: 0
  failedJobsHistoryLimit: 2
  jobTemplate:
    spec:
      template:
       spec:
        containers:
        - name: fss-scheduler
          image: aboovv/fss-snapshot-scheduler
          command: [ "python" ]
          args: [ "fss-scheduler.py" ]
          env:
            - name: OCI_USER_ID
              value: <user ocid from ~/.oci/config>
            - name: OCI_KEY
              value: <paste output of cat ~/.oci/pvt_key.pem | base64 -w 0>
            - name: OCI_KEY_DIGEST
              value: <fingerprint from ~/.oci/config>
            - name: OCI_TENANCY_ID
              value: <tenancy ocid from ~/.oci/config>
            - name: OCI_REGION
              value: <oci region>
            - name: OCI_COMPARTMENT_ID
              value: <compartment ocid of the FSS resources>
            - name: FSS_CKPT_SHCEDULER_CFG
              value: <json string for the checkpoint schedule>
        restartPolicy: Never
$
```
## Defining the schedule

The schedule can be defined in two ways. One is using configuration file **schedule.cfg**. The file name can be overridden with environment variable **FSS_CKPT_SHCEDULER_CFG_FILE**

### Format 

> *[\<OCID Of the FS\>]*  
> *SnapshotPrefix1 = frequency:expiry*  
> *SnapshotPrefix2 = frequency:expiry*  
> *SnapshotPrefix3 = frequency:expiry*  
> *...*  

The Snapshots created by the scheduler will start with Snapshot prefix.

#### Example cfg file

> *[ocid1.filesystem.oc1.iad.aaaaaaaaaac2b2xbnfqwillqojxwiotjmfsc2ylefuzaaaaa] # FSName: FS1*  
> *Hourly_Snapshot = 1h:1d*  
> *Daily_Snapshot =  1d:1m*  
> *Monthly_SnapShot = 1m:6m*  
> *[ocid1.filesystem.oc1.iad.aaaaaaaaaaczrj4infqwillqojxwiotjmfsc2ylefuzaaaaa] # FSName: FS2*  
> *Monthly_SnapShot = 1m:2y*  
> *Yearly_SnapShot = 1y:1c*  

The *Hourly_Snapshot = 1h:1d* entry above will create snapshot every hour and keep it for a day. h for hour, d for day, m for month, y for year and c for century. 

Another option to specify the schedules without this config file is using environment variable **FSS_CKPT_SHCEDULER_CFG**. This will be handy if the scheduler is started in docker or as a Kubernettes cron job

The *FSS_CKPT_SHCEDULER_CFG* carries the above cfg file entries in json format. 

#### Example:

The following encoded string is equivalent to the above cfg file. 

> FSS_CKPT_SHCEDULER_CFG='{"ocid1.filesystem.oc1.iad.aaaaaaaaaac2b2xbnfqwillqojxwiotjmfsc2ylefuzaaaaa": {"hourly_snapshot": "1h:1d", "daily_snapshot": "1d:1m", "monthly_snapshot": "1m:6m"},"ocid1.filesystem.oc1.iad.aaaaaaaaaaczrj4infqwillqojxwiotjmfsc2ylefuzaaaaa": {"monthly_snapshot": "1m:2y", "yearly_snapshot": "1y:1c"}}'

## OCI API authentication

The OCI CLI/API access needs to be configured. Refer [Configuring the CLI](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliconfigure.htm) . The DEFAULT section is all needed if the script is used as a standalone in a system. However, if it is used from a container, the OCI config values should be passed as the environment variables. 

These are the environment variables and the values can be directly copied from the OCI config file (*~/.oci/config*)

> OCI_USER_ID=\<user ocid from ~/.oci/config\>  
> OCI_TENANCY_ID=\<tenancy ocid from ~/.oci/config\>  
> OCI_KEY_DIGEST=\<fingerprint from ~/.oci/config\>  
> OCI_REGION=\<oci region\>  
> OCI_COMPARTMENT_ID=\<compartment ocid of the FSS resources\>  
> OCI_KEY=\<paste output of * cat ~/.oci/pvt_key.pem | base64 -w 0 * \>  
  
## Image

The Docker file is provided. However, the image is available at ***aboovv/fss-snapshot-scheduler***

## Standalone script cronjob

Configure it for every hour as follows. The user for which this crontab is configured should have configured OCI CLI access. [Configuring the CLI](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliconfigure.htm). If its not configured, the OCI environment variables should be configured for authentication. 

```
0 * * * *  python /home/opc/scheduler/fss-scheduler.py
```

## Kubernetes cron job

If the scheduler to be run as a kubernetes job, a sample k8s-cron.yaml file is included along with this. The environment variables section needs to be filled. If feels insecure, use Kubernetes secrets for these environment variables instead. 


