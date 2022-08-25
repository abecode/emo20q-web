#!/usr/bin/env python3

"""This file automates some of the deployment tasks

for it to work, fabric 2.x should be installed

also, you should have an aws account, awscli, and ssh keys

pip install fabric awscli

fab spin-up-ami
fab get-ip
# first ssh-add ~/.ssh/ust-aws.pem
fab -H ec2-user@ip-address install-software
"""

import os
import time
import invoke
from invoke import run
import patchwork.transfers

#REGION = os.environ.get("REGION", "us-east-2")
PROFILE = "ust"
#PROFILE = "default"
APP_NAME = "emo20q-staging"
#INSTANCE_TYPE = "t2.micro"
#INSTANCE_TYPE = "t3a.medium"
INSTANCE_TYPE = "t3a.large"
AMI = "ami-02d1e544b84bf7502" # aws linux as of 2022-07-13


@invoke.task
def get_ip(c):
    """runs aws ec2 describe instances to get the ip addresses of running
    instances with name emo20q

    """
    result = run(f"aws --profile {PROFILE} ec2 describe-instances --filter 'Name=tag:Name,Values={APP_NAME}' 'Name=instance-state-name,Values=running' --query 'Reservations[*].Instances[*].[PublicIpAddress]' --output text",
                 echo=True).stdout.strip()
    print(result)
    return result


@ invoke.task
def spin_up_server(c):
    """ spins up a server if there isn't one aready """
    ipaddress = get_ip(c)
    if ipaddress:
        return ipaddress
    #result = run(f"aws --profile {PROFILE} ec2 run-instances --image-id {AMI} --count 1 --instance-type t2.micro --key-name ust-aws --query 'Instances[0].InstanceId'", echo=True)
    result = run(f"aws --profile {PROFILE} ec2 run-instances --image-id {AMI} --count 1 --instance-type {INSTANCE_TYPE}  --key-name ust-aws --query 'Instances[0].InstanceId'", echo=True)
    #t3a.medium
    print(result)
    #pdb.set_trace()
    instance_id = result.stdout.strip()
    time.sleep(10)
    run(f"aws --profile {PROFILE} ec2 create-tags --resources {instance_id} --tags Key=Name,Value={APP_NAME}", echo=True)
    time.sleep(10)
    result = run(f"aws --profile {PROFILE} ec2 describe-instances --filter 'Name=tag:Name,Values={APP_NAME}' 'Name=instance-state-name,Values=running' --query 'Reservations[*].Instances[*].[PublicIpAddress]' --output text",
        echo=True).stdout.strip()
    print(result)
    return result
    
@ invoke.task
def terminate_server(c):
    """ spins down a server if there is one """
    ipaddress = get_ip(c)
    if not ipaddress:
        print("there are no instances")
        return
    result = run(f"aws --profile {PROFILE} ec2 describe-instances --filter 'Name=tag:Name,Values={APP_NAME}' 'Name=instance-state-name,Values=running' --query 'Reservations[*].Instances[*].InstanceId' --output text")
    instance_id = result.stdout.strip()
    answer = input("terminating instance " + instance_id + ": y/n\n")
    if answer.lower().startswith("y"):
        result = run(f"aws --profile {PROFILE} ec2 terminate-instances --instance-ids {instance_id}", echo=True)
        print(result)
        return result
    else:
        print("aborted")

@invoke.task
def install_software_basics(c):
    c.sudo("yum -y update", echo=True)
    c.sudo("yum -y install git", echo=True)
    c.sudo("yum -y install emacs-nox", echo=True)
    c.sudo("yum -y install python3 python3-pip", echo=True)
    c.run("echo escape ^Bb > ~/.screenrc")
    # c.sudo("yum -y install zlib-devel libjpeg-devel make gcc-c++ python3-devel")
    # c.run("[ -f Miniconda3-latest-Linux-x86_64.sh ] || wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh", echo=True)
    # c.run("chmod +x Miniconda3-latest-Linux-x86_64.sh", echo=True)
    # c.run("[ -d /home/ec2-user/miniconda3 ] || ./Miniconda3-latest-Linux-x86_64.sh", echo=True)
    # #c.run("pip3 install --user Pillow requests numpy")
    # # maybe numpy is installed by conda??  conda seems like it's
    # # designed to deal with a lot of the dependencies so some of these
    # # might be redundant
    # c.run("/home/ec2-user/miniconda3/bin/conda install -q pytorch torchvision -c pytorch")
    c.sudo("yum install -y python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools", echo=True)
    c.sudo("yum install -y gcc gcc-c++ make", echo=True) # equiv to build-essential
    c.sudo("yum install -y python3-devel", echo=True)
    c.run("pip3 install  gevent gevent-websocket", echo=True)
    c.sudo("yum install -y pcre-devel")
    c.sudo("yum install -y openssl-devel") # https://stackoverflow.com/questions/24183053/how-to-build-uwsgi-with-ssl-support-to-use-the-websocket-handshake-api-function
    c.run("pip3 install wheel uwsgi", echo=True)
    c.sudo("amazon-linux-extras enable epel", echo=True)
    c.sudo("yum clean metadata", echo=True)
    c.sudo("yum install -y epel-release", echo=True)

@invoke.task
def git_clone(c):
    """ run this manually to double check """
    # c.forward_agent = True
    # c.run("ssh-keygen -F github.com || ssh-keyscan github.com >>~/.ssh/known_hosts", echo=True)
    # c.run("git init", echo=True)
    # c.run("git remote add origin git@github.com:abecode/twitter-api-experiment.git", echo=True)
    # c.run("git fetch", echo=True)
    # c.run("git pull --ff-only origin master", echo=True)
    # c.run("git checkout master", echo=True)
    # c.run("git reset --hard HEAD", echo=True)
    c.run("git clone https://github.com/abecode/emo20q-web", echo=True)
    c.run("cd emo20q-web && git clone https://github.com/abecode/emo20q",
          echo=True)
    c.run("cd emo20q-web && pip3 install -r requirements.awsprod.txt",
          echo=True)
    # note: due to python3.7 on aws, networkx only available > 2.6
    
@invoke.task
def install_webserver_software(c):
    # stuff for uwsgi,
    # c.f. https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-uswgi-and-nginx-on-ubuntu-18-04
    c.sudo("yum install -y nginx", echo=True) # https://devcoops.com/install-nginx-on-aws-ec2-amazon-linux/
    # also https://stackoverflow.com/questions/17413526/nginx-missing-sites-available-directory
    c.sudo("mkdir -p /var/www/emo20q.org/html", echo=True)
    c.sudo("chown -R $USER:$USER /var/www/emo20q.org/html", echo=True)
    c.sudo("chmod -R 755 /var/www", echo=True)
    c.sudo("mkdir /etc/nginx/sites-available")
    c.sudo("mkdir /etc/nginx/sites-enabled")
    c.sudo("chown  $USER:$USER /etc/nginx/sites-available", echo=True)
    c.sudo("chown  $USER:$USER /etc/nginx/sites-enabled", echo=True)
    c.run("cp /home/ec2-user/emo20q-web/emo20q-nginx /etc/nginx/sites-available",
          echo=True)
    c.sudo("ln -s /etc/nginx/sites-available/emo20q-nginx /etc/nginx/sites-enabled",
           echo=True)
    #c.sudo("perl -i.bak -pe '$_ =~ s|(http {)|$1\n\tinclude /etc/nginx/sites-enabled/*;|' /etc/nginx/nginx.conf", echo=True) # inplace edit nginx with perl
    #c.sudo("perl -i.bak2 -pe 'BEGIN{$start=0};/# Settings for a TLS/...END and $_ =~ s/^#(?! Settings)//' /etc/nginx/nginx.conf", echo=True) # more perl foo to uncomment tls section
    c.sudo("usermod -a -G $USER nginx", echo=True)
    c.sudo("mv  /etc/nginx/nginx.conf /etc/nginx/nginx.conf_bak", echo=True)
    c.sudo("cp /home/ec2-user/emo20q-web/nginx.conf /etc/nginx/", echo=True)
    c.sudo("systemctl enable nginx.service", echo=True)
    c.sudo("systemctl start nginx.service", echo=True)
    c.sudo("yum install -y python-certbot-nginx", echo=True)
    #c.sudo("sudo certbot --nginx -d emo20q.org -d www.emo20q.org", echo=True)
    
    # this is the cmd I've been using for the webserver:
    # uwsgi --http :5000 --gevent 200 --http-websockets --master --wsgi-file flask-socket.py --callable app
    # don't really know exactly what it does or if there are better settings!
    # also cf uwsgi -i uwsgi.ini : there is examples of using unix sockets
    # taking out master makes uswgi easier to kill:
    # uwsgi --http :5000 --gevent 200  --wsgi-file flask_answerer_api.py --callable app

@ invoke.task
def cp_model(c):
    """copy model to aws """
    #c.put("/Users/kaze7539/Downloads/saved_model_bert_emo20qa", "/home/ec2-user")
    patchwork.transfers.rsync(c, "/Users/kaze7539/Downloads/saved_model_bert_emo20qa", "/home/ec2-user")
