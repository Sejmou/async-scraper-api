import aiohttp


async def get_ip() -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://ipinfo.io/json") as response:
            data = await response.json()
            ip = data["ip"]
            assert isinstance(ip, str)

    return ip
