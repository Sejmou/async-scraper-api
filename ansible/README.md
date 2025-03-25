# Ansible Playbooks for Scraper Node Management
The Scraper API is intended to be run on separate machines, each with their own IP. This allows us to fetch/scrape data from multiple IPs at once.

In this folder, you can find basic config code required so that the Docker containers (Compose projects) and [Ansible](https://github.com/ansible/ansible) playbooks to deploy (and update, if necessary) the `api-server` from a central 'control node' to multiple 'scraper nodes' (i.e. machines accessible via SSH).

To do that, you need to have Ansible installed on the machine you want to use as your control node. You can install Ansible on Ubuntu by running the following command:

```bash
sudo apt update
sudo apt install ansible
```

After that, you will need to create an `inventory.ini`, building on the example provided in `inventory.ini.example`. The file should contain the IP addresses of the machines you want to use, in two separate sections (as defined in the example file):
1. `machines_to_configure`: machines that haven't been configured yet (i.e. they don't have Docker installed, the repository cloned, etc.).
2. `scrapers`: machines that have been configured and are ready to run the scraper API.

Note that you do NOT have to install ansible on the scraper nodes. The nodes aren't even aware they are being controlled by Ansible.

## Setting up new scrapers
The `./configure_new_scrapers.yml` playbook sets up new scrapers. It does the following:
1. Install Docker and Docker Compose + make some sensible configuration changes.
2. Clone this repository.
3. Build and run the Docker Compose project.

```bash
ansible-playbook -i inventory.ini configure_new_scrapers.yml
```

Make sure to move the scrapers that still need to be configured to the `to_configure` group in the `inventory.ini` file.

## Updating the scrapers
The `./scraper_update.yml` playbook updates the scrapers by pulling the latest changes from the GitHub repository and rebuilding/restarting the Docker containers.

You can run it via the following command:

```bash
ansible-playbook -i inventory.ini scraper_update.yml
```

Make sure to move the scrapers that you want to update (and have been configured already) to the `scrapers` group in the `inventory.ini` file.