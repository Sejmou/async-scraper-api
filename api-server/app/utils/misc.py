import requests

# NOTE: while the use of the sync (and hence blocking) requests library is discouraged,
# the IP getter functions here are an exception as they are meant to be used only once at startup and are not performance-critical.


def get_public_ip_from_ipinfo() -> str:
    """
    Gets the public IP address of the host machine from ipinfo.io.
    """
    response = requests.get("https://ipinfo.io/json", timeout=1)
    data = response.json()
    return data["ip"]


def get_public_ip_from_ifconfig() -> str:
    """
    Gets the public IP address of the host machine from the API endpoint at ifconfig.io.
    """
    response = requests.get("https://ifconfig.io/ip", timeout=1)
    return response.text.strip()


def get_public_ip_from_icanhazip() -> str:
    """
    Gets the public IP address of the host machine from the API endpoint at icanhazip.com.
    """
    response = requests.get("https://icanhazip.com", timeout=1)
    return response.text.strip()


def get_public_ip_from_ipify() -> str:
    """
    Gets the public IP address of the host machine from the API endpoint at ipify.org.
    """
    response = requests.get("https://api.ipify.org?format=json")
    data = response.json()
    return data["ip"]


def get_public_ip() -> str:
    """
    Gets the public IP address of the host machine. Tries multiple services until one works.
    """
    try:
        return get_public_ip_from_ifconfig()
    except requests.exceptions.RequestException:
        pass

    try:
        return get_public_ip_from_icanhazip()
    except requests.exceptions.RequestException:
        pass

    try:
        return get_public_ip_from_ipinfo()
    except requests.exceptions.RequestException:
        pass

    try:
        return get_public_ip_from_ipify()
    except requests.exceptions.RequestException:
        pass

    raise Exception("Could not get public IP address from any service.")
