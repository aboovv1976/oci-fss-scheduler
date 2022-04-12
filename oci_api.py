
import configparser
import logging
import os
import stat
import oci
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


