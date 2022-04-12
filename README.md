# OCI FSS Scheduler

This is a script used to create and delete FSS snapshots based on a pre-defined schedule. The scheduler can be used in three ways.

1. As a stand alone script - fss-scheduler.py. This can be placed in cron job to run every one hour. The script will create and delete (expire) snapshots as defined in scheduler.cfg file or using FSS_CKPT_SHCEDULER_CFG= environment variable.

2. This includes a Dockerfile that can be used to build a docker image. This is based on alpine Linux and includes all the required modules including oci api. Run the docker image every hour.

3. Run in K8s cluster with the above docker image  as cron job 

## Usage

In its simplest form, just copy the fss-scheduler.py, oci_api.py and schedule.cfg and then modify the schedule.cfg with FS ocid and schedule details.  Run fss-scheduler.py (one time use) or install it in cron to run every hour. The OCI API python modules should be installed. See [OCI SDK for Python](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/pythonsdk.htm). 

The advantage of using docker image is that it comes with all the modules installed and should not have any other dependancies. 

### docker

> sudo docker run -it --env-file env iad.ocir.io/fsssolutions/fss-sn-scheduler

This will run just once but requires the above to be installed as a cronjob. The env file should be populated as mentioned in the next section. That is *FSS_CKPT_SHCEDULER_CFG* and OCI authentication environment variables. 

### Kubernetes

kubectl apply -f k8s-cron.yaml

The environment variables should be updated in the k8s-cron.yaml file. See the next sections for the required environment variable. That is *FSS_CKPT_SHCEDULER_CFG* and OCI authentication environment variables. 

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

The Docker file is provided. However, the image is available at ***iad.ocir.io/fsssolutions/fss-sn-scheduler***

## Kubernetes cron job

If the scheduler to be run as a kubernetes job, a sample k8s-cron.yaml file is included along with this. The environment variables section needs to be filled. If feels insecure, use Kubernetes secrets for these environment variables instead. 