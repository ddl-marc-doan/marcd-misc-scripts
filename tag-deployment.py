#!/usr/bin/env python3
import argparse
import boto3
import jmespath

parser = argparse.ArgumentParser(description='Tag resources related to a specific customer deployment')

parser.add_argument('--region', '-r',help='AWS Region to search', default='us-west-2',required=False)
parser.add_argument('--customer-name','-c',help='Value for the customer name to tag to resources',required=True)
parser.add_argument('--deploy-id','-d',help='Deploy ID to search for resources to tag',required=True)
args = vars(parser.parse_args())
aws_region = args['region']
cust_name = args['customer_name']
deploy_id = args['deploy_id']

sts = boto3.client('sts')
acct_num = sts.get_caller_identity()['Account']
ec2 = boto3.client('ec2')
asg = boto3.client('autoscaling')
rsgapi = boto3.client('resourcegroupstaggingapi')

asgs = asg.describe_auto_scaling_groups(
    Filters = [
        {'Name':'tag:deploy_id','Values':[deploy_id]}
    ]
)

asg_list = [i['AutoScalingGroupName'] for i in asgs['AutoScalingGroups']]
print(f'Found ASGs with deploy_id={deploy_id}: {asg_list}')
for group in asg_list:
    resp = asg.create_or_update_tags(
        Tags = [
            {
                'Key': 'customer_name',
                'Value': cust_name,
                'ResourceId': group,
                'ResourceType': 'auto-scaling-group',
                'PropagateAtLaunch': True 
            }
        ]
    )
    print(f'Updated ASG {asg}: Response {resp}')

ec2s = ec2.describe_instances(
    Filters = [
        {'Name':'tag:deploy_id','Values':[deploy_id]}
    ]
)
ec2_list = []
for res in ec2s['Reservations']:
    for instance in res['Instances']:
        ec2_list.append(instance['InstanceId'])

print(f'Found EC2 instances with deploy_id={deploy_id}: {ec2_list}')
ec2_arns = [f'arn:aws:ec2:{aws_region}:{acct_num}:instance/{i}' for i in ec2_list]

vpcs = ec2.describe_vpcs(
    Filters = [
        {'Name':'tag:deploy_id','Values':[deploy_id]}
    ]
)
vpc_list = [i['VpcId'] for i in vpcs['Vpcs']]
vpc_arns = [f'arn:aws:ec2:{aws_region}:{acct_num}:vpc/{i}' for i in vpc_list]
print(f'Found VPCs with deploy_id={deploy_id}: {vpc_list}')

natgws = ec2.describe_nat_gateways(
    Filters = [
        {'Name':'tag:deploy_id','Values':[deploy_id]}
    ]
)
natgw_list = [i['NatGatewayId'] for i in natgws['NatGateways']]
natgw_arns = [f'arn:aws:ec2:{aws_region}:{acct_num}:natgateway/{i}' for i in natgw_list]
print(f'Found NATGWs with deploy_id={deploy_id}: {natgw_list}')

res_list = ec2_arns + vpc_arns + natgw_arns

print('Tagging ASGs, VPCs, instances shown above...')
rsg_resp = rsgapi.tag_resources(
    ResourceARNList = res_list,
    Tags = {
        'customer_name':cust_name
    }
)
print(f'Updated resources {res_list}: Response {rsg_resp}')