---
layout: default
title: Download Data from NODE SOP
parent: SOPs
---

# Downloading data from Node

[NODE](https://www.biosino.org/node/index) allows to download up to 2GB via https so `sftp` is the only viable option to retrieve a dataset.
No instructions for that are available in NODE so this SOP is the result of communication with the Node support team

#### Requirements:
- **NODE credentials**: required to authenticate and connect to the ftp server. You can register through NODE or using this [link](https://www.biosino.org/bmdcRegist/register)
- **`lftp`**: it's already installed in the EC2 instance, to install in on a Mac see the instructions [here](https://brewinstall.org/install-lftp-on-mac-with-brew/)
- **a list of the target run IDs**: after logging into Node this can be downloaded for any public dataset 

### Step 1 :  Connecting to the server

```
$ lftp
lftp :~> connect sftp://fms.biosino.org:44398
lftp fms.biosino.org:~> login your-username
Password: ****
```
The username is the full email you used to sign in to NODE

### Step 2 : Find the files
For each project there is a folder in the format `/Public/byrun/OEXX/OERXXXX/` where X is a single digit. The project folder contains a folder per run accession, each of them containing the fastq files for that run.

You can list the content of the project folder to check if all the expected files are there.
As an example command: with glob you can specify the pattern to identify all the files and list them with find.
```bash
lftp your-username@fms.biosino.org:~> glob find  /Public/byrun/OEXX/OERXXXX/OERXXXX*/*.fq.gz
```


### Step 3 : Get the files
This step can require a lot of time so it's better to execute it from a screen terminal.

Select the files with the same pattern as above and download them with `pget` to your local directory. 
You can check your local directory with `lpwd` and change it with the command `lcd`
```bash
lftp your-username@fms.biosino.org:~> glob pget /Public/byrun/OEXX/OERXXXX/OERXXXX*/*.fq.gz
```
