import argparse
import configparser


def generate_ssh_config(
    inventory_file: str, identity_file: str = "~/.ssh/id_rsa"
) -> None:
    """
    Generates and prints SSH config entries from an Ansible inventory file.

    Args:
        inventory_file (str): Path to the inventory.ini file.
        identity_file (str): Path to the SSH identity file.
    """
    # Parse the inventory file
    config = configparser.ConfigParser(allow_no_value=True, delimiters=(" ", "="))
    config.read(inventory_file)

    # Iterate through each section and host
    for section in config.sections():
        print(f"# --- section: {section} ---")  # Print the section name as a comment
        for host, properties in config.items(section):
            if not properties:  # Skip invalid entries
                continue

            # Parse key-value pairs (like ansible_host and ansible_user)
            host_vars = dict(item.split("=") for item in properties.split())

            # Extract ansible_host and ansible_user (default values as fallback)
            ansible_host: str = host_vars.get("ansible_host", "unknown_host")
            ansible_user: str = host_vars.get("ansible_user", "root")

            # Print the SSH config entry
            print(f"Host {host.lower().replace('_', '-')}")
            print(f"    HostName {ansible_host}")
            print(f"    User {ansible_user}")
            print(f"    IdentityFile {identity_file}")
            print()  # Add a blank line for spacing


def main() -> None:
    """
    Parse command-line arguments and call the SSH config generator.
    """
    parser = argparse.ArgumentParser(
        description="Generate and print SSH config from an Ansible inventory file."
    )

    # Argument for the inventory file
    parser.add_argument(
        "-i",
        "--inventory",
        type=str,
        default="inventory.ini",
        help="Path to the Ansible inventory file (default: inventory.ini)",
    )

    # Argument for the identity file
    parser.add_argument(
        "-k",
        "--identity-file",
        type=str,
        default="~/.ssh/id_rsa",
        help="Path to the SSH identity file (default: ~/.ssh/id_rsa)",
    )

    args = parser.parse_args()

    # Generate and print the SSH config
    generate_ssh_config(args.inventory, args.identity_file)


if __name__ == "__main__":
    main()
