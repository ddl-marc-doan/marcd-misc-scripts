#!/usr/bin/env python3

import argparse
import boto3
import json

parser = argparse.ArgumentParser(description='Search the Availability Zones in a given AWS region for a specific instance type')

parser.add_argument('--region', '-r',help='AWS Region to search', default='us-west-2',required=False)
parser.add_argument('--instance-type','-i',help='EC2 instance type to check',default='t3.large',required=False)
args = vars(parser.parse_args())
aws_region = args['region']
ec2_type = args['instance_type']

api_client = boto3.setup_default_session(region_name=aws_region)
api_client = boto3.client('ec2')

az_list_from_api = api_client.describe_availability_zones()
az_list = [list_entry['ZoneName'] for list_entry in az_list_from_api['AvailabilityZones']]

ec2_is_here = []
ec2_list_from_api = api_client.describe_instance_type_offerings(LocationType='availability-zone',Filters=[{'Name':'location','Values':az_list},{'Name':'instance-type','Values':[ec2_type]}])
ec2_is_here = [ location_dict['Location'] for location_dict in ec2_list_from_api['InstanceTypeOfferings'] ]

print(f"EC2 instance type: {ec2_type}\n"
      f"Region: {aws_region} \n"
      f"AZs: {ec2_is_here}")
