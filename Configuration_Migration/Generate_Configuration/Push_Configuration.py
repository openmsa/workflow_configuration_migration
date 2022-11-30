import json
import re
import os.path
from msa_sdk import constants
from msa_sdk.order import Order
from msa_sdk.device import Device
from msa_sdk.variables import Variables
from msa_sdk.msa_api import MSA_API
from msa_sdk.conf_profile import ConfProfile
from pathlib import Path
import sys

'''
Generic Function to extract Section information like Class-Map, Policy-Map, Router-Policy
'''
def extractSection(inputList,startString,endString):
    flag =0
    outDict = {}
    for item in inputList:
        if re.search(r'^' + startString,item):
            flag = 1
            itemArray = item.split(' ')
            if 'class-map' in startString:
                key =  itemArray[2]
            elif 'extcommunity-set' in startString:
                key =  itemArray[2]
            elif 'community-set' in startString:
                key =  itemArray[1]
            else:
                key =  itemArray[1]
            outDict[key] = '!\n'
        if (re.search(r'^' + endString,item) and flag == 1):
            flag = 0
            outDict[key] = outDict[key] + item + '\n'
            outDict[key] = outDict[key] + '!' + '\n'
        if flag == 1:
            outDict[key] = outDict[key] + item + '\n'
    return outDict



def lookUpPOP(routerSource):
    if routerSource == 'i-br-sp-spo-mrb-rsd-01':
        DD = '11'
        POP = '16885:1159'
    elif routerSource == 'i-br-df-bsa-tco-rsd-01':
        DD = '61'
        POP = '16885:1612'
    elif routerSource == 'i-br-rj-rjo-bar-rsd-01':
        DD = '21'
        POP = '16885:1211'
    elif routerSource == 'i-br-sp-spo-jgr-rsd-01':
        DD = '11'
        POP = '16885:1156'
    elif routerSource == 'i-br-sp-spo-sef-rsd-01':
        DD = '11'
        POP = '16885:1158'
    elif routerSource == 'i-br-sp-spo-vun-rsd-01':
        DD = '11'
        POP = '16885:1150'
    elif routerSource == 'i-br-sp-cas-cst-rsd-01':
        DD = '19'
        POP = '16885:1147'
    elif routerSource == 'i-br-rj-rjo-gsr-rsd-01':
        DD = '21'
        POP = '16885:1216'
    elif routerSource == 'i-br-sp-spo-ibr-rsd-01':
        DD = '11'
        POP = '16885:1152'
    elif routerSource == 'i-br-sp-spo-con-rsd-01':
        DD = '11'
        POP = '16885:1151'
    elif routerSource == 'i-br-go-gna-srh-rsd-01':
        DD = '62'
        POP = '16885:1621'
    elif routerSource == 'i-br-es-vta-bfe-rsd-01':
        DD = '27'
        POP = '16885:1271'
    elif routerSource == 'i-br-mg-ula-utp-rsd-01':
        DD = '31'
        POP = '16885:1341'
    elif routerSource == 'i-br-pa-blm-ccp-rsd-01':
        DD = '91'
        POP = '16885:1911'
    elif routerSource == 'i-br-pe-rce-rce-rsd-01':
        DD = '81'
        POP = '16885:1811'
    elif routerSource == 'i-br-sc-bnu-bnu-rsd-01':
        DD = '47'
        POP = '16885:1471'
    elif routerSource == 'i-br-sc-soo-fns-rsd-01':
        DD = '48'
        POP = '16885:1486'
    elif routerSource == 'i-br-sp-soc-sgn-rsd-01':
        DD = '14'
        POP = '16885:1140'
    elif routerSource == 'i-br-sp-spo-vgu-rsd-01':
        DD = '11'
        POP = '16885:1163'
    else:
        DD = '0'
        POP = '0'
    return DD,POP

def replaceCommunity(full_message,DD,POP):
    newLines = []
    newcommunities = { 
                     '10429:114':'16885:1114',
                     '10429:115':'16885:1115',
                     '10429:116':'16885:1116',
                     '10429:132':'16885:1132',
                     '10429:133':'16885:1133',
                     '10429:134':'16885:1134',
                     '10429:135':'16885:1135',
                     '10429:136':'16885:1136',
                     '10429:137':'16885:1137',
                     '10429:138':'16885:1138',
                     '10429:139':'16885:1139',
                     '10429:140':'16885:1140',
                     '10429:141':'16885:1141',
                     '10429:142':'16885:1142',
                     '10429:143':'16885:1143',
                     '10429:144':'16885:1144',
                     '10429:145':'16885:1145',
                     '10429:146':'16885:1146',
                     '10429:147':'16885:1147',
                     '10429:149':'16885:1149',
                     '10429:150':'16885:1150',
                     '10429:151':'16885:1151',
                     '10429:152':'16885:1152',
                     '10429:153':'16885:1153',
                     '10429:154':'16885:1154',
                     '10429:155':'16885:1155',
                     '10429:156':'16885:1156',
                     '10429:157':'16885:1157',
                     '10429:158':'16885:1158',
                     '10429:159':'16885:1159',
                     '10429:160':'16885:1160',
                     '10429:162':'16885:1162',
                     '10429:163':'16885:1163',
                     '10429:164':'16885:1164',
                     '10429:165':'16885:1165',
                     '10429:166':'16885:1166',
                     '10429:167':'16885:1167',
                     '10429:168':'16885:1168',
                     '10429:169':'16885:1169',
                     '10429:170':'16885:1170',
                     '10429:171':'16885:1171',
                     '10429:174':'16885:1174',
                     '10429:190':'16885:1190',
                     '10429:199':'16885:1199',
                     '10429:211':'16885:1211',
                     '10429:212':'16885:1212',
                     '10429:213':'16885:1213',
                     '10429:221':'16885:1214',
                     '10429:936':'16885:1215',
                     '10429:937':'16885:1216',
                     '10429:221':'16885:1221',
                     '10429:222':'16885:1222',
                     '10429:223':'16885:1223',
                     '10429:938':'16885:1241',
                     '10429:227':'16885:1271',
                     '10429:288':'16885:1288',
                     '10429:311':'16885:1311',
                     '10429:312':'16885:1312',
                     '10429:313':'16885:1313',
                     '10429:939':'16885:1314',
                     '10429:941':'16885:1315',
                     '10429:942':'16885:1316',
                     '10429:321':'16885:1321',
                     '10429:943':'16885:1322',
                     '10429:323':'16885:1323',
                     '10429:944':'16885:1331',
                     '10429:341':'16885:1341',
                     '10429:351':'16885:1351',
                     '10429:371':'16885:1371',
                     '10429:411':'16885:1411',
                     '10429:412':'16885:1412',
                     '10429:413':'16885:1413',
                     '10429:945':'16885:1414',
                     '10429:946':'16885:1415',
                     '10429:416':'16885:1416',
                     '10429:948':'16885:1421',
                     '10429:431':'16885:1431',
                     '10429:949':'16885:1432',
                     '10429:950':'16885:1441',
                     '10429:951':'16885:1451',
                     '10429:952':'16885:1452',
                     '10429:471':'16885:1471',
                     '10429:472':'16885:1472',
                     '10429:953':'16885:1473',
                     '10429:954':'16885:1474',
                     '10429:481':'16885:1481',
                     '10429:482':'16885:1482',
                     '10429:955':'16885:1483',
                     '10429:956':'16885:1484',
                     '10429:957':'16885:1485',
                     '10429:511':'16885:1511',
                     '10429:251':'16885:1512',
                     '10429:960':'16885:1513',
                     '10429:961':'16885:1514',
                     '10429:958':'16885:1515',
                     '10429:959':'16885:1516',
                     '10429:962':'16885:1531',
                     '10429:541':'16885:1541',
                     '10429:963':'16885:1542',
                     '10429:964':'16885:1551',
                     '10429:611':'16885:1611',
                     '10429:612':'16885:1612',
                     '10429:161':'16885:1613',
                     '10429:966':'16885:1615',
                     '10429:621':'16885:1621',
                     '10429:968':'16885:1622',
                     '10429:967':'16885:1623',
                     '10429:631':'16885:1631',
                     '10429:641':'16885:1641',
                     '10429:642':'16885:1642',
                     '10429:651':'16885:1651',
                     '10429:969':'16885:1652',
                     '10429:661':'16885:1661',
                     '10429:671':'16885:1671',
                     '10429:970':'16885:1672',
                     '10429:271':'16885:1711',
                     '10429:371':'16885:1712',
                     '10429:971':'16885:1713',
                     '10429:972':'16885:1751',
                     '10429:791':'16885:1791',
                     '10429:973':'16885:1792',
                     '10429:181':'16885:1811',
                     '10429:975':'16885:1812',
                     '10429:974':'16885:1813',
                     '10429:281':'16885:1821',
                     '10429:976':'16885:1822',
                     '10429:831':'16885:1831',
                     '10429:978':'16885:1832',
                     '10429:977':'16885:1833',
                     '10429:841':'16885:1841',
                     '10429:979':'16885:1842',
                     '10429:185':'16885:1851',
                     '10429:980':'16885:1852',
                     '10429:910':'16885:1910',
                     '10429:911':'16885:1911',
                     '10429:920':'16885:1920',
                     '10429:921':'16885:1921',
                     '10429:981':'16885:1981',
                     '10429:113':"10429:40000',\n   ios-regex  '10429:400DD',\n   ios-regex 'POP",
                     '10429:112':"10429:40000',\n   ios-regex  '10429:400DD',\n   ios-regex '10429:58300',\n   ios-regex '10429:583DD',\n   ios-regex 'POP", 
                     '10429:122':"10429:40000',\n   ios-regex  '10429:400DD',\n   ios-regex '10429:58300',\n   ios-regex '10429:583DD',\n   ios-regex 'POP",
                     '10429:108':"10429:30000',\n   ios-regex  '10429:300DD',\n   ios-regex '10429:58100',\n   ios-regex '10429:581DD',\n   ios-regex 'POP",
                     '10429:109':"10429:30000',\n   ios-regex  '10429:300DD',\n   ios-regex '10429:58400',\n   ios-regex '10429:584DD',\n   ios-regex '10429:58300',\n   ios-regex '10429:583DD',\n   ios-regex 'POP",
                     '10429:110':"10429:30000',\n   ios-regex  '10429:300DD'|'10429:30000',\n   ios-regex '10429:300DD',\n   ios-regex '10429:58400',\n   ios-regex '10429:584DD',\n   ios-regex '10429:58300',\n   ios-regex '10429:583DD',\n   ios-regex '10429:58100',\n   ios-regex '10429:581DD',\n   ios-regex 'POP",
                     '10429:120':"10429:30000',\n   ios-regex  '10429:300DD',\n   ios-regex '10429:58300',\n   ios-regex '10429:583DD',\n   ios-regex '10429:58100',\n   ios-regex '10429:581DD',\n   ios-regex '10429:58400',\n   ios-regex '10429:584DD',\n   ios-regex 'POP",
                     '10429:121':"10429:300DD',\n   ios-regex  '10429:58400',\n   ios-regex '10429:584DD',\n   ios-regex '10429:58300',\n   ios-regex '10429:583DD',\n   ios-regex 'POP",
                     '10429:123':"10429:586DD',\n   ios-regex  '10429:65511"
                     }

    newcommunitiesOut = { 
                     '10429:114':'16885:1114',
                     '10429:115':'16885:1115',
                     '10429:116':'16885:1116',
                     '10429:132':'16885:1132',
                     '10429:133':'16885:1133',
                     '10429:134':'16885:1134',
                     '10429:135':'16885:1135',
                     '10429:136':'16885:1136',
                     '10429:137':'16885:1137',
                     '10429:138':'16885:1138',
                     '10429:139':'16885:1139',
                     '10429:140':'16885:1140',
                     '10429:141':'16885:1141',
                     '10429:142':'16885:1142',
                     '10429:143':'16885:1143',
                     '10429:144':'16885:1144',
                     '10429:145':'16885:1145',
                     '10429:146':'16885:1146',
                     '10429:147':'16885:1147',
                     '10429:149':'16885:1149',
                     '10429:150':'16885:1150',
                     '10429:151':'16885:1151',
                     '10429:152':'16885:1152',
                     '10429:153':'16885:1153',
                     '10429:154':'16885:1154',
                     '10429:155':'16885:1155',
                     '10429:156':'16885:1156',
                     '10429:157':'16885:1157',
                     '10429:158':'16885:1158',
                     '10429:159':'16885:1159',
                     '10429:160':'16885:1160',
                     '10429:162':'16885:1162',
                     '10429:163':'16885:1163',
                     '10429:164':'16885:1164',
                     '10429:165':'16885:1165',
                     '10429:166':'16885:1166',
                     '10429:167':'16885:1167',
                     '10429:168':'16885:1168',
                     '10429:169':'16885:1169',
                     '10429:170':'16885:1170',
                     '10429:171':'16885:1171',
                     '10429:174':'16885:1174',
                     '10429:190':'16885:1190',
                     '10429:199':'16885:1199',
                     '10429:211':'16885:1211',
                     '10429:212':'16885:1212',
                     '10429:213':'16885:1213',
                     '10429:221':'16885:1214',
                     '10429:936':'16885:1215',
                     '10429:937':'16885:1216',
                     '10429:221':'16885:1221',
                     '10429:222':'16885:1222',
                     '10429:223':'16885:1223',
                     '10429:938':'16885:1241',
                     '10429:227':'16885:1271',
                     '10429:288':'16885:1288',
                     '10429:311':'16885:1311',
                     '10429:312':'16885:1312',
                     '10429:313':'16885:1313',
                     '10429:939':'16885:1314',
                     '10429:941':'16885:1315',
                     '10429:942':'16885:1316',
                     '10429:321':'16885:1321',
                     '10429:943':'16885:1322',
                     '10429:323':'16885:1323',
                     '10429:944':'16885:1331',
                     '10429:341':'16885:1341',
                     '10429:351':'16885:1351',
                     '10429:371':'16885:1371',
                     '10429:411':'16885:1411',
                     '10429:412':'16885:1412',
                     '10429:413':'16885:1413',
                     '10429:945':'16885:1414',
                     '10429:946':'16885:1415',
                     '10429:416':'16885:1416',
                     '10429:948':'16885:1421',
                     '10429:431':'16885:1431',
                     '10429:949':'16885:1432',
                     '10429:950':'16885:1441',
                     '10429:951':'16885:1451',
                     '10429:952':'16885:1452',
                     '10429:471':'16885:1471',
                     '10429:472':'16885:1472',
                     '10429:953':'16885:1473',
                     '10429:954':'16885:1474',
                     '10429:481':'16885:1481',
                     '10429:482':'16885:1482',
                     '10429:955':'16885:1483',
                     '10429:956':'16885:1484',
                     '10429:957':'16885:1485',
                     '10429:511':'16885:1511',
                     '10429:251':'16885:1512',
                     '10429:960':'16885:1513',
                     '10429:961':'16885:1514',
                     '10429:958':'16885:1515',
                     '10429:959':'16885:1516',
                     '10429:962':'16885:1531',
                     '10429:541':'16885:1541',
                     '10429:963':'16885:1542',
                     '10429:964':'16885:1551',
                     '10429:611':'16885:1611',
                     '10429:612':'16885:1612',
                     '10429:161':'16885:1613',
                     '10429:966':'16885:1615',
                     '10429:621':'16885:1621',
                     '10429:968':'16885:1622',
                     '10429:967':'16885:1623',
                     '10429:631':'16885:1631',
                     '10429:641':'16885:1641',
                     '10429:642':'16885:1642',
                     '10429:651':'16885:1651',
                     '10429:969':'16885:1652',
                     '10429:661':'16885:1661',
                     '10429:671':'16885:1671',
                     '10429:970':'16885:1672',
                     '10429:271':'16885:1711',
                     '10429:371':'16885:1712',
                     '10429:971':'16885:1713',
                     '10429:972':'16885:1751',
                     '10429:791':'16885:1791',
                     '10429:973':'16885:1792',
                     '10429:181':'16885:1811',
                     '10429:975':'16885:1812',
                     '10429:974':'16885:1813',
                     '10429:281':'16885:1821',
                     '10429:976':'16885:1822',
                     '10429:831':'16885:1831',
                     '10429:978':'16885:1832',
                     '10429:977':'16885:1833',
                     '10429:841':'16885:1841',
                     '10429:979':'16885:1842',
                     '10429:185':'16885:1851',
                     '10429:980':'16885:1852',
                     '10429:910':'16885:1910',
                     '10429:911':'16885:1911',
                     '10429:920':'16885:1920',
                     '10429:921':'16885:1921',
                     '10429:981':'16885:1981',
                     '10429:113':"10429:40000,10429:400DD,POP",
                     '10429:112':"10429:40000,10429:400DD,10429:58300,10429:583DD,POP", 
                     '10429:122':"10429:40000,10429:400DD,10429:58300,10429:583DD,POP",
                     '10429:108':"10429:30000,10429:300DD,10429:58100,10429:581DD,POP",
                     '10429:109':"10429:30000,10429:300DD,10429:58400,10429:584DD,10429:58300,10429:583DD,POP",
                     '10429:110':"10429:30000,10429:300DD,10429:58400,10429:584DD,10429:58300,10429:583DD,10429:58100,10429:581DD,POP",
                     '10429:120':"10429:30000,10429:300DD,10429:58300,10429:583DD,10429:58100,10429:581DD,10429:58400,10429:584DD,POP",
                     '10429:121':"10429:300DD,10429:58400,10429:584DD,10429:58300,10429:583DD,POP",
                     '10429:123':"10429:586DD,10429:65511"
                     }
                     

                     
    newLines = []
    flagCommunity = 0
    full_message_List = full_message.split('\n')
    community = {}
    community = extractSection(full_message_List,'community-set','end-set')



    #Delete Community-Set information From original text
    for line in full_message_List:
        if  flagCommunity == 0 and 'community-set' not in line:
            newLines.append(line)
        if 'community-set' in line:
            flagCommunity = 1
        if 'end-set' in line and  flagCommunity == 1 :
            flagCommunity = 0

    #Process Comunity-set
    for communityName,communityset in community.items():
        for k,v in newcommunities.items():
            v = v.replace('DD',DD)
            v = v.replace('POP',POP)
            if re.search(k,communityset):
                if k == '10429:110':
                    vList = v.split('|')
                    if 'CLIENTES_BGP' in communityset:
                        newCommunity = vList[0]
                    else:
                        newCommunity = vList[1]
                else:
                    newCommunity = v
                newcommunityset = communityset.replace(k,newCommunity)
                community[communityName] = newcommunityset

    #text without community-set, replace CLIENTES_BGP, and communities with communityOut
    full_message_without_communities = ''
    for item in newLines:
        item = item.rstrip()
        if item != '':
            item = item.replace('CLIENTES_BGP','CLIENTES')
        full_message_without_communities  = full_message_without_communities + item + '\n'
        
    #Replace Communities in any place of Text
    for k,v in newcommunitiesOut.items():
        if re.search(k,full_message_without_communities):
            v = v.replace('DD',DD)
            v = v.replace('POP',POP)
            full_message_without_communities = full_message_without_communities.replace(k,v)
            
    #Regenerate community-set  replace CLIENTES_BGP
    new_message = '!############# MS community_set #############\n'

    for communityName,communityset in community.items():
        if communityName == 'CLIENTES_BGP':
            communityset = communityset.replace('CLIENTES_BGP','CLIENTES')
        new_message = new_message + communityset 
    new_message = new_message + 'root\n'

    #Concat to text without communit-set
    new_message = new_message + full_message_without_communities
    
    return new_message    


currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from common.common import *

dev_var = Variables()

context = Variables.task_call(dev_var)

if not context.get('push_to_device'):
  context['push_to_device'] = 'false'

push_to_device = context['push_to_device']



#check if the folder  DIRECTORY exist, else create it
if not os.path.isdir(DIRECTORY):
 os.mkdir(DIRECTORY)
 
timeout = 3600

subtenant_ref = context["UBIQUBEID"]
subtenant_id = context["UBIQUBEID"][4:]

device_id_full = context['destination_device_id']

device_id = device_id_full[3:]
# instantiate device object
obmf  = Order(device_id=device_id)

if ((context['real_device_source'] == 'false' or context['real_device_source'] == False ) and  (context['real_source_and_real_destination'] == 'false' or context['real_source_and_real_destination'] == False )) and (context['push_to_device']== 'true' or context['push_to_device']== True):
  msg = 'ERROR: Before to push the configuration to real device '+str(device_id_full)+', you should Import first the configuration from real device '+str(context['source_device_id'])
  create_event(device_id_full, "1", "MIGRATION", "GEN_CONFIG",  subtenant_ref, subtenant_id, msg)
  context['push_to_device'] = 'false'        #reset value
  MSA_API.task_error(msg, context, True)

context['push_to_device'] = 'false'        #reset value

MS_list        = context['MS_list']  
MS_list        = MS_list.replace(' ;',';')     
MS_list        = MS_list.replace('; ',';')     
command = 'CREATE'
 
MS_source_path = context['MS_source_path']
MS_imported =[]

####### GEt the list of MS attached to the destination device:
# Get deployment settings ID for the device.
deployment_settings_id = obmf.command_get_deployment_settings_id()
context['destination_deployment_settings_id'] = deployment_settings_id

if not deployment_settings_id:
  msg = 'ERROR: There is no deployement setting for the managed entity '+device_id_full
  create_event(device_id_full, "1", "MIGRATION", "GEN_CONFIG",  subtenant_ref, subtenant_id, msg)
  MSA_API.task_error(msg, context, True)
  
#Get all microservices attached to this deployment setting.
confprofile  = ConfProfile(deployment_settings_id)
all_ms_attached = confprofile.read()
all_ms_attached = json.loads(all_ms_attached)
MS_list_destination=[]
MS_list_destination_order = {}
all_order = {}
if all_ms_attached.get("microserviceUris"):
  all_ms_attached = all_ms_attached["microserviceUris"] 
  #context[ 'MS_attached destination device_id' + device_id + ' : '] = all_ms_attached
  # all_ms_attached = {        "CommandDefinition/LINUX/CISCO_IOS_XR_emulation/address_family.xml": {"name": "address_family","groups": ["EMULATION","CISCO", "IOS"],"order": 0,"importRank": 10},
  
  if all_ms_attached:
    # We should sort by the value 'importRank', but we can have many MS with samed importRank values
    for full_ms, MS in all_ms_attached.items():
      if Path(full_ms).stem:
        importRank = MS['importRank']
        if MS_list_destination_order.get(importRank):
          MS_list_destination_order[importRank].append(Path(full_ms).stem)
        else:
          MS_list_destination_order[importRank] = []
          MS_list_destination_order[importRank].append(Path(full_ms).stem)
      
    if MS_list_destination_order:
      orderlist = sorted(MS_list_destination_order.keys())
      for importRank in orderlist:
        if  MS_list_destination_order.get(importRank):
          for  val in MS_list_destination_order[importRank]:
            MS_list_destination.append(val)   
            
context['MS_list_destination']  = MS_list_destination

ms_not_attached_destination_device = []
full_message = ''
customer=context['customer_id_instance_id']
full_message = full_message + '!############# ' + customer +  ' ############# \n'

if (push_to_device == 'true' or push_to_device == True):
  mode = 2  #mode=2 : Apply to device and in DB
else:
  mode = 1  #mode=1 : Apply only in hte DB, not applied on the device
         
hostnameSourceDict = json.loads(context.get('hostname_values_serialized'))
for k,v in hostnameSourceDict.items() :
    hostnameSource = k

if MS_list:
  for MS in  MS_list_destination:
    if MS and MS in MS_list.split(';'):
      if context.get( MS + '_values_serialized') and context[MS + '_values_serialized'] != '{}':
        config = json.loads(context.get( MS + '_values_serialized')) 
        params = dict()
        params[MS] = config
        #context[MS + '_export_params'] = params
        modestatic = 1  
        obmf.command_call(command, modestatic, params, timeout) 
   
        response = json.loads(obmf.content)
        #context[ MS + '_generate_response'] = response
        # bgp_vrf_generate_response": {
          # "entity": {
              # "commandId": 0,
              # "status": "OK",
              # "message": "\n!\nip vrf  TRIBUNAL-JUSTICA\n\n#exit\n!\n!\nip vrf  V1038:Bco_Bradesco\n\n#exit\n!\n!\nip vrf  V4815:Sabesp_Intragov\n  rd  \n\n  export map  \n#exit\n!"
          # },
          
        if response.get("entity"):
          if response.get("entity").get("status") and response["entity"]["status"] == "OK":
           if response.get("entity").get("message"):
            # response =    "message": "\nip vrf  V4815:Sabesp_Intragov\n  description  \n  rd  \n\n    route-target export 10429:11048 \n     route-target import 10429:102 \n     route-target import 10429:11048 \n \n\n  export map  \n"
            message =  response.get("entity").get("message") 
            message = re.sub('\s+\n', '\n', message, flags=re.UNICODE)  #remove blank lines
            message = re.sub('  \s+', '  ', message, flags=re.UNICODE)  #remove more than 2 blank space, but  \s+ remove also newline

            full_message = full_message + '\n!############# MS ' + MS+  ' #############\n'  + message

          else:
            msg = 'ERROR: Cannot run CREATE on microservice: '+ MS + ', response='+ str(response)
            create_event(device_id_full, "1",  "MIGRATION", "GEN_CONFIG",  subtenant_ref, subtenant_id, msg)
            MSA_API.task_error(msg , context, True)
        else: 
          if 'wo_newparams' in response:
            msg = 'ERROR: Cannot run CREATE on microservice: '+ MS + ', response='+ str(response.get('wo_newparams'))
            create_event(device_id_full, "1", "MIGRATION", "GEN_CONFIG", subtenant_ref, subtenant_id, msg)
            MSA_API.task_error(msg, context, True)
          else:
            msg = 'ERROR: Cannot run CREATE on microservice: '+ MS + ', response='+ str(response)
            create_event(device_id_full, "1", "MIGRATION", "GEN_CONFIG", subtenant_ref, subtenant_id, msg)
            MSA_API.task_error(msg , context, True)
    else:
      ms_not_attached_destination_device.append(MS)
    
#Change Communities only if router is a RSD
DD,POP = lookUpPOP(hostnameSource)
if DD != '0':
    full_message = replaceCommunity(full_message,DD,POP)
    #pass
#Change some IPV4 acccess list name
if 'ipv4 access-list 120' in full_message:
    full_message = full_message.replace('ipv4 access-list 120','ipv4 access-list FILTRO_BGP_PACKETS_IPv4')
if 'ipv4 access-list 121' in full_message:
    full_message = full_message.replace('ipv4 access-list 121','ipv4 access-list FILTRO_PFX_MARTIANS_IPv4')
if 'ipv4 access-list 122' in full_message:
    full_message = full_message.replace('ipv4 access-list 122','ipv4 access-list FILTRO_CIDR_VIVO_IPv4')
if 'ipv4 access-list 123' in full_message:
    full_message = full_message.replace('ipv4 access-list 123','ipv4 access-list FILTRO_PFX_INFRA_IPv4')
# match access-group ipv4 - class-map
if 'match access-group ipv4 120' in full_message:
    full_message = full_message.replace('match access-group ipv4 120','match access-group ipv4 FILTRO_BGP_PACKETS_IPv4')
if 'match access-group ipv4 121' in full_message:
    full_message = full_message.replace('match access-group ipv4 121','match access-group ipv4 FILTRO_PFX_MARTIANS_IPv4')
if 'match access-group ipv4 122' in full_message:
    full_message = full_message.replace('match access-group ipv4 122','match access-group ipv4 FILTRO_CIDR_VIVO_IPv4')
if 'match access-group ipv4 123' in full_message:
    full_message = full_message.replace('match access-group ipv4 123','match access-group ipv4 FILTRO_PFX_INFRA_IPv4')        
#Change some IPV6 acccess list name    
if 'ipv6 access-list 120' in full_message:
    full_message = full_message.replace('ipv6 access-list 120','ipv6 access-list FILTRO_BGP_PACKETS_IPv6')
if 'ipv6 access-list 121' in full_message:
    full_message = full_message.replace('ipv6 access-list 121','ipv6 access-list FILTRO_PFX_MARTIANS_IPv6')
if 'ipv6 access-list 122' in full_message:
    full_message = full_message.replace('ipv6 access-list 122','ipv6 access-list FILTRO_CIDR_VIVO_IPv6')
if 'ipv6 access-list 123' in full_message:
   full_message = full_message.replace('ipv6 access-list 123','ipv6 access-list FILTRO_PFX_INFRA_IPv6')
# match access-group ipv6 - class-map
if 'match access-group ipv6 120' in full_message:
    full_message = full_message.replace('match access-group ipv6 120','match access-group ipv6 FILTRO_BGP_PACKETS_IPv6')
if 'match access-group ipv6 121' in full_message:
    full_message = full_message.replace('match access-group ipv6 121','match access-group ipv6 FILTRO_PFX_MARTIANS_IPv6')
if 'match access-group ipv6 122' in full_message:
    full_message = full_message.replace('match access-group ipv6 122','match access-group ipv6 FILTRO_CIDR_VIVO_IPv6')
if 'match access-group ipv6 123' in full_message:
    full_message = full_message.replace('match access-group ipv6 123','match access-group ipv6 FILTRO_PFX_INFRA_IPv6')        


#Create the global config file :
if mode == 2:
    #Apply conf to Destination Device
    xrDestination = Device(device_id=device_id)
    data = dict(configuration=full_message)
    xrDestination.push_configuration(json.dumps(data))

f = open(context['generate_file'], "w")
f.write(full_message)
f.close()

if ms_not_attached_destination_device:
  if (push_to_device == 'true' or push_to_device == True):
    context['pushed_to_destination_device'] = 'true'    
    MSA_API.task_success('Applied to device, WARNING, some microservices ('+';'.join(ms_not_attached_destination_device)+') not found for destination device :'+device_id_full+', other microservice imported successfully ('+';'.join(MS_imported)+')', context, True)
  else:
    MSA_API.task_success('SIMULATED, WARNING , some microservices ('+';'.join(ms_not_attached_destination_device)+') not found for destination device :'+device_id_full+', other microservice imported successfully ('+';'.join(MS_imported)+')', context, True)
else:
  if (push_to_device == 'true' or push_to_device == True):
    context['pushed_to_destination_device'] = 'true'    
    MSA_API.task_success('Applied to device DONE, microservices ('+MS_list+') imported for managed entity: '+device_id_full, context, True)
  else:
    MSA_API.task_success('SIMULATED, DONE, microservices ('+MS_list+') imported for managed entity: '+device_id_full, context, True)
  



