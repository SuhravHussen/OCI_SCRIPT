# Configuration - All hardcoded as requested
availabilityDomains = ["Jmgg:AP-SINGAPORE-1-AD-1"]
displayName = 'myfreevps'
compartmentId = 'ocid1.tenancy.oc1..aaaaaaaajhlubohcmqe6djhhasqw2ikpoh4mpiweyi4qmpi7si3tetajltaq'
subnetId = 'ocid1.subnet.oc1.ap-singapore-1.aaaaaaaaalwdnywyzlzz5i4ebpgmdqn6ldxgvhzrwoyub72jccs5f2ft52rq'
ssh_authorized_keys = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC0COjULtWaQSWk3LjDJotu8K4Sc/489SKTFpXWWAY8uQUcGjk9bzaL9ydJHgMyDERfauLD9nN6Q1U4ga0TPJ8aAa67sdob+/V7VriXAoSYfJH4YtzI/Wi64vUXj41I18qnhhpdstBsixzpQb2uEoMPQtkRmHyJmpxu9FG5RxXV16hs39wDDv3cfc63cmcFE0ahFoQaQA+C6UsutoFzww/ziHv6kcbyy8LQMNipcHc64V97RH3uacPfY8x+B1LJuxwvYkYmCLisPUmxnstp69FUHzoHIiUZpZvt76al4I+p6RYopk4zixwqqh1yqu8POAX6tKtFN7ErdUggm6Ly4pgT ssh-key-2025-11-03"

imageId = "ocid1.image.oc1.ap-singapore-1.aaaaaaaa5a3xwkk5vaichk47fms2uzvsqeriats2uorf6kwgq3l3nwrbhipa"
boot_volume_size_in_gbs="xxxx"
boot_volume_id="xxxx"

bot_token = "xxxx"
uid = "xxxx"

ocpus = 4
memory_in_gbs = 24

minimum_time_interval = 1

import oci
import logging
import time
import sys
import telebot
import datetime
import os
from flask import Flask, jsonify, request

# Initialize Flask app
app = Flask(__name__)

# Initialize Telegram bot
bot = telebot.TeleBot(bot_token) if bot_token != "xxxx" else None

# Configure logging
LOG_FORMAT = '[%(levelname)s] %(asctime)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Global variables for OCI clients (initialized once)
config = None
to_launch_instance = None
identity_client = None
vnc_client = None
volume_client = None
cloud_name = None
email = None

def initialize_oci_clients():
    """Initialize OCI clients once at startup"""
    global config, to_launch_instance, identity_client, vnc_client, volume_client, cloud_name, email

    logging.info("#####################################################")
    logging.info("Initializing OCI clients for web server")

    logging.info("Loading OCI config")
    config = oci.config.from_file(file_location="./config")

    logging.info("Initialize service client with default config file")
    to_launch_instance = oci.core.ComputeClient(config)
    identity_client = oci.identity.IdentityClient(config)
    vnc_client = oci.core.VirtualNetworkClient(config)
    volume_client = oci.core.BlockstorageClient(config)

    cloud_name = identity_client.get_tenancy(tenancy_id=compartmentId).data.name
    email = identity_client.list_users(compartment_id=compartmentId).data[0].email

    logging.info(f"OCI clients initialized for account: {cloud_name} ({email})")

def try_create_instance():
    """
    Attempt to create an Oracle Cloud instance once.
    Returns a dict with status, message, and details.
    """
    try:
        # Check available storage
        total_volume_size = 0
        logging.info("Check available storage in account")

        if imageId != "xxxx":
            try:
                list_volumes = volume_client.list_volumes(compartment_id=compartmentId).data
            except Exception as e:
                if isinstance(e, oci.exceptions.ServiceError):
                    error_msg = f"{e.status} - {e.code} - {e.message}"
                else:
                    error_msg = f"{type(e).__name__}: {str(e)}"
                logging.error(error_msg)
                return {
                    "status": "error",
                    "message": "Failed to check storage",
                    "error": error_msg
                }

            if list_volumes:
                for block_volume in list_volumes:
                    if block_volume.lifecycle_state not in ("TERMINATING", "TERMINATED"):
                        total_volume_size += block_volume.size_in_gbs

            for availabilityDomain in availabilityDomains:
                list_boot_volumes = volume_client.list_boot_volumes(
                    availability_domain=availabilityDomain,
                    compartment_id=compartmentId
                ).data
                if list_boot_volumes:
                    for b_volume in list_boot_volumes:
                        if b_volume.lifecycle_state not in ("TERMINATING", "TERMINATED"):
                            total_volume_size += b_volume.size_in_gbs

            free_storage = 200 - total_volume_size
            if boot_volume_size_in_gbs != "xxxx" and free_storage < boot_volume_size_in_gbs:
                error_msg = f"Insufficient storage: {free_storage} GB free, need {boot_volume_size_in_gbs} GB"
                logging.critical(error_msg)
                return {"status": "error", "message": error_msg}

            if boot_volume_size_in_gbs == "xxxx" and free_storage < 47:
                error_msg = f"Insufficient storage: {free_storage} GB free, need 47 GB"
                logging.critical(error_msg)
                return {"status": "error", "message": error_msg}

        # Check current instances
        logging.info("Check current instances in account")
        current_instance = to_launch_instance.list_instances(compartment_id=compartmentId)
        response = current_instance.data

        total_ocpus = total_memory = _A1_Flex = 0
        instance_names = []

        if response:
            logging.info(f"{len(response)} instance(s) found!")
            for instance in response:
                logging.info(f"{instance.display_name} - {instance.shape} - {int(instance.shape_config.ocpus)} ocpu(s) - {instance.shape_config.memory_in_gbs} GB(s) | State: {instance.lifecycle_state}")
                instance_names.append(instance.display_name)
                if instance.shape == "VM.Standard.A1.Flex" and instance.lifecycle_state not in ("TERMINATING", "TERMINATED"):
                    _A1_Flex += 1
                    total_ocpus += int(instance.shape_config.ocpus)
                    total_memory += int(instance.shape_config.memory_in_gbs)
            logging.info(f"Current: {_A1_Flex} active VM.Standard.A1.Flex instance(s)")
        else:
            logging.info("No instance(s) found!")

        logging.info(f"Total ocpus: {total_ocpus} - Total memory: {total_memory} GB || Free {4-total_ocpus} ocpus - Free memory: {24-total_memory} GB")

        # Validate resource limits
        if total_ocpus + ocpus > 4 or total_memory + memory_in_gbs > 24:
            error_msg = "Total maximum resource exceed free tier limit (Over 4 ocpus/24GB total)"
            logging.critical(error_msg)
            return {"status": "error", "message": error_msg}

        if displayName in instance_names:
            error_msg = f"Duplicate display name: {displayName}"
            logging.critical(error_msg)
            return {"status": "error", "message": error_msg}

        logging.info(f"Precheck pass! Attempting to create VM.Standard.A1.Flex: {ocpus} ocpus - {memory_in_gbs} GB")

        # Prepare instance source details
        if imageId != "xxxx":
            if boot_volume_size_in_gbs == "xxxx":
                op = oci.core.models.InstanceSourceViaImageDetails(source_type="image", image_id=imageId)
            else:
                op = oci.core.models.InstanceSourceViaImageDetails(
                    source_type="image",
                    image_id=imageId,
                    boot_volume_size_in_gbs=boot_volume_size_in_gbs
                )

        if boot_volume_id != "xxxx":
            op = oci.core.models.InstanceSourceViaBootVolumeDetails(
                source_type="bootVolume",
                boot_volume_id=boot_volume_id
            )

        # Try to create instance in each availability domain
        for availabilityDomain in availabilityDomains:
            instance_detail = oci.core.models.LaunchInstanceDetails(
                metadata={"ssh_authorized_keys": ssh_authorized_keys},
                availability_domain=availabilityDomain,
                shape='VM.Standard.A1.Flex',
                compartment_id=compartmentId,
                display_name=displayName,
                is_pv_encryption_in_transit_enabled=True,
                source_details=op,
                create_vnic_details=oci.core.models.CreateVnicDetails(
                    assign_public_ip=True,
                    subnet_id=subnetId
                ),
                shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
                    ocpus=ocpus,
                    memory_in_gbs=memory_in_gbs
                )
            )

            try:
                logging.info(f"Attempting to launch instance in {availabilityDomain}...")
                launch_instance_response = to_launch_instance.launch_instance(instance_detail)

                # Wait for instance to initialize
                time.sleep(60)

                # Get instance IP
                list_vnic_attachments_response = to_launch_instance.list_vnic_attachments(
                    compartment_id=compartmentId,
                    instance_id=launch_instance_response.data.id
                )
                list_private_ips_response = vnc_client.list_private_ips(
                    subnet_id=subnetId,
                    vnic_id=list_vnic_attachments_response.data[0].vnic_id
                )
                get_public_ip_response = vnc_client.get_public_ip_by_private_ip_id(
                    get_public_ip_by_private_ip_id_details=oci.core.models.GetPublicIpByPrivateIpIdDetails(
                        private_ip_id=list_private_ips_response.data[0].id
                    )
                )
                ip = get_public_ip_response.data.ip_address

                success_msg = f'"{displayName}" VPS created successfully! IP: {ip}'
                logging.info(success_msg)

                # Send Telegram notification
                if bot and uid != "xxxx":
                    try:
                        telegram_msg = f'''✅ "{displayName}" VPS created successfully!
Cloud Account: {cloud_name}
Email: {email}
VPS IP: {ip}
Time (UTC): {datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}'''
                        bot.send_message(uid, telegram_msg)
                    except Exception as e:
                        logging.warning(f"Failed to send Telegram notification: {e}")

                return {
                    "status": "success",
                    "message": success_msg,
                    "ip": ip,
                    "instance_name": displayName,
                    "cloud_account": cloud_name,
                    "email": email
                }

            except oci.exceptions.ServiceError as e:
                error_msg = f'{e.status} - {e.code} - {e.message}'
                logging.info(error_msg)

                if e.status == 500 and "Out of host capacity" in str(e.message):
                    return {
                        "status": "out_of_capacity",
                        "message": "Out of host capacity - will retry on next trigger",
                        "error": error_msg
                    }

                return {
                    "status": "failed",
                    "message": "Instance creation failed",
                    "error": error_msg
                }

            except Exception as e:
                error_msg = f'Unexpected error: {str(e)}'
                logging.error(error_msg)
                return {
                    "status": "failed",
                    "message": "Instance creation failed",
                    "error": error_msg
                }

        return {
            "status": "failed",
            "message": "Failed to create instance in all availability domains"
        }

    except Exception as e:
        error_msg = f'Critical error: {str(e)}'
        logging.error(error_msg)
        return {
            "status": "error",
            "message": "Critical error occurred",
            "error": error_msg
        }


# Flask Routes
@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Oracle Cloud Instance Creator",
        "message": "Web server is running. Use POST /trigger to attempt instance creation.",
        "cloud_account": cloud_name if cloud_name else "Not initialized",
        "email": email if email else "Not initialized"
    }), 200


@app.route('/trigger', methods=['GET'])
def trigger_instance_creation():
    """Trigger endpoint to attempt instance creation. Always returns HTTP 200."""
    logging.info("=" * 60)
    logging.info("Instance creation triggered via HTTP request")
    logging.info("=" * 60)

    # Ensure OCI clients are initialized when running under gunicorn
    try:
        if any(client is None for client in (to_launch_instance, identity_client, vnc_client, volume_client)):
            initialize_oci_clients()
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        logging.error(f"Failed to initialize OCI clients: {err}")
        return jsonify({
            "status": "error",
            "message": "OCI clients not initialized. Check config and private_key.pem files.",
            "error": err
        }), 200

    result = try_create_instance()

    # Always return HTTP 200; the actual status is conveyed in the JSON body
    return jsonify(result), 200


if __name__ == '__main__':
    # Initialize OCI clients at startup
    try:
        initialize_oci_clients()
        logging.info("OCI clients initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize OCI clients: {e}")
        logging.error("Check your config file and private_key.pem file")
        sys.exit(1)

    # Get port from environment (Render requirement) with fallback
    port = int(os.environ.get('PORT', 10000))

    logging.info(f"Starting Flask web server on port {port}")
    logging.info("Endpoints:")
    logging.info("  GET / - Health check")
    logging.info("  GET /trigger - Trigger instance creation")

    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False)