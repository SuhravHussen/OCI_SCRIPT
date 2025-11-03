from flask import Flask
import threading
import os

# ===========================================
# DUMMY WEB SERVER (required for Koyeb Web Service)
# ===========================================
app = Flask(__name__)

@app.get("/")
def ok():
    return "running"

# ===========================================
# ORIGINAL SCRIPT STARTS
# ===========================================

availabilityDomains = ["Jmgg:AP-SINGAPORE-1-AD-1"]
displayName = 'myfreevps'
compartmentId = os.getenv("OCI_COMPARTMENT_ID")
subnetId = os.getenv("OCI_SUBNET_ID")
ssh_authorized_keys = os.getenv("SSH_KEY")

imageId = os.getenv("OCI_IMAGE_ID")
boot_volume_size_in_gbs="xxxx"
boot_volume_id="xxxx"

bot_token = os.getenv("BOT_TOKEN")
uid = os.getenv("TG_UID")

ocpus = 4
memory_in_gbs = 24

minimum_time_interval = 1

import oci
import logging
import time
import sys
import telebot
import datetime

bot = telebot.TeleBot(bot_token)

LOG_FORMAT = '[%(levelname)s] %(asctime)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[ logging.StreamHandler(sys.stdout) ]
)

def run_bot():
    logging.info("### Script to spawn VM.Standard.A1.Flex instance ###")
    message = f'Start spawning instance VM.Standard.A1.Flex - {ocpus} ocpus - {memory_in_gbs} GB'
    logging.info(message)

    logging.info("Loading OCI config")
    config = oci.config.from_file(file_location="./config")

    to_launch_instance = oci.core.ComputeClient(config)
    identity_client = oci.identity.IdentityClient(config)
    vnc_client = oci.core.VirtualNetworkClient(config)
    cloud_name = identity_client.get_tenancy(tenancy_id=compartmentId).data.name
    email = identity_client.list_users(compartment_id=compartmentId).data[0].email

    volume_client = oci.core.BlockstorageClient(config)
    total_volume_size = 0

    logging.info("Check available storage in account")

    if imageId != "xxxx":
        try:
            list_volumes = volume_client.list_volumes(compartment_id=compartmentId).data
        except Exception as e:
            logging.info(f"{e.status} - {e.code} - {e.message}")
            sys.exit()

        if list_volumes != []:
            for block_volume in list_volumes:
                if block_volume.lifecycle_state not in ("TERMINATING", "TERMINATED"):
                    total_volume_size += block_volume.size_in_gbs

        for ad in availabilityDomains:
            list_boot_volumes = volume_client.list_boot_volumes(availability_domain=ad, compartment_id=compartmentId).data
            if list_boot_volumes != []:
                for b_volume in list_boot_volumes:
                    if b_volume.lifecycle_state not in ("TERMINATING", "TERMINATED"):
                        total_volume_size += b_volume.size_in_gbs

    current_instance = to_launch_instance.list_instances(compartment_id=compartmentId)
    response = current_instance.data

    total_ocpus = total_memory = _A1_Flex = 0
    instance_names = []

    if response:
        for instance in response:
            instance_names.append(instance.display_name)
            if instance.shape == "VM.Standard.A1.Flex" and instance.lifecycle_state not in ("TERMINATING","TERMINATED"):
                _A1_Flex += 1
                total_ocpus += int(instance.shape_config.ocpus)
                total_memory += int(instance.shape_config.memory_in_gbs)

    if total_ocpus + ocpus > 4 or total_memory + memory_in_gbs > 24:
        logging.critical("Exceed free limits")
        sys.exit()

    if displayName in instance_names:
        logging.critical("Duplicate display name. Exit.")
        sys.exit()

    if imageId != "xxxx":
        op = oci.core.models.InstanceSourceViaImageDetails(source_type="image", image_id=imageId)
    if boot_volume_id != "xxxx":
        op = oci.core.models.InstanceSourceViaBootVolumeDetails(source_type="bootVolume", boot_volume_id=boot_volume_id)

    wait_s_for_retry = 1
    tc = oc = total_count = j_count = 0

    if bot_token != "xxxx" and uid != "xxxx":
        try:
            msg = f'''Cloud Account Name :- {cloud_name}
Email :- {email}
Number of Retry :- {total_count}
Bot Status :- Running
Last Checked (UTC): {datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}'''
            msg_id = bot.send_message(uid, msg).id
        except:
            pass

    while True:
        for ad in availabilityDomains:
            instance_detail = oci.core.models.LaunchInstanceDetails(
                metadata={"ssh_authorized_keys": ssh_authorized_keys},
                availability_domain=ad,
                shape='VM.Standard.A1.Flex',
                compartment_id=compartmentId,
                display_name=displayName,
                is_pv_encryption_in_transit_enabled=True,
                source_details=op,
                create_vnic_details=oci.core.models.CreateVnicDetails(assign_public_ip=True, subnet_id=subnetId),
                shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(ocpus=ocpus, memory_in_gbs=memory_in_gbs)
            )
            try:
                launch_instance_response = to_launch_instance.launch_instance(instance_detail)
                time.sleep(60)
                list_vnic_attachments_response = to_launch_instance.list_vnic_attachments(compartment_id=compartmentId,instance_id=launch_instance_response.data.id)
                list_private_ips_response = vnc_client.list_private_ips(subnet_id=subnetId,vnic_id=list_vnic_attachments_response.data[0].vnic_id)
                get_public_ip_response = vnc_client.get_public_ip_by_private_ip_id(
                    get_public_ip_by_private_ip_id_details=oci.core.models.GetPublicIpByPrivateIpIdDetails(private_ip_id=list_private_ips_response.data[0].id))
                ip = get_public_ip_response.data.ip_address

                logging.info(f'"{displayName}" VPS created, IP: {ip}')
                sys.exit()

            except Exception:
                time.sleep(wait_s_for_retry)

# Run script in background thread
threading.Thread(target=run_bot, daemon=True).start()

# Start web server (keeps Koyeb container alive)
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
